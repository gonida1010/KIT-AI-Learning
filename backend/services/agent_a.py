"""
Agent A — 행정 및 커리어 멘토.
RAG 기반 응답 · 유사도 기반 멀티 초이스 · 정보 큐레이션(학원 업로드 PDF) 제공.
큐레이션 검색은 FAISS 벡터 유사도 + LLM 의도 분석 기반.
"""

import logging
from datetime import datetime, timedelta, timezone

_KST = timezone(timedelta(hours=9))

from services.llm_provider import LLMProvider, extract_json
from services.rag import search_curation_vectorstore, search_mentor_vectorstore, search_mentor_basic_vectorstore
from db.store import store

logger = logging.getLogger(__name__)

CURATION_SCHEDULE = {
    0: "채용정보",
    1: "IT뉴스",
    2: "AI타임스",
    3: "자격증·공모전",
    4: "개발트렌드",
}

AGENT_A_PROMPT = """\
당신은 국비지원(KDT) 코딩 학원의 'Agent A — 행정 및 커리어 멘토'입니다.
학원 관련 행정, 취업, 자격증, 공모전, 학원 규정 질문에 답변합니다.

[지식 베이스 문맥]
{context}

[큐레이션 정보]
{curation}

[멘토 전용 자료]
{mentor_materials}

[응답 규칙]
1. 질문이 모호하면 3~4개의 구체적 선택지를 제시하세요.
2. 구체적 질문에는 즉시 답변하고 관련 자료가 있으면 안내하세요.
3. 큐레이션(채용정보, IT뉴스, AI 타임스 등) 요청 시 저장된 데이터를 제공하세요.
   놓친 자료 요청 시 해당 날짜·주제를 명확히 알려주세요.
4. 감정적 상담이 필요해 보이면 멘토 상담을 안내하세요.
5. 답변은 간결하면서도 유용하게 작성하세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "content": "답변 메시지 텍스트",
  "choices": [
    {{"label": "선택지 제목", "description": "선택지 설명"}}
  ],
  "needs_handoff": false,
  "related_docs": ["관련 자료명"],
    "curation_refs": ["참조 큐레이션 ID"],
    "mentor_doc_refs": ["멘토 자료 ID"]
}}

- choices 불필요 시 빈 배열 [].
- needs_handoff true 시 감정적 상담 필요.
"""


def _search_mentor_materials(user_id: str | None, message: str) -> tuple[str, list[dict], list[dict]]:
    """멘토 최신 자료 + 기초 자료를 모두 검색. Returns (context_text, latest_docs, basic_docs)."""
    if not user_id:
        return "(멘토 전용 자료 없음)", [], []

    user = store.get_user(user_id)
    mentor_id = (user or {}).get("mentor_id")
    if not mentor_id:
        return "(연결된 멘토 없음)", [], []

    # 최신 자료 검색
    results = search_mentor_vectorstore(mentor_id, message, k=3)
    latest_docs = []
    seen_ids: set[str] = set()
    lines = []
    for result in results:
        doc_id = result.get("mentor_doc_id", "")
        if doc_id in seen_ids:
            continue
        mentor_doc = store.get_mentor_doc(doc_id)
        if not mentor_doc:
            continue
        seen_ids.add(doc_id)
        latest_docs.append(mentor_doc)
        lines.append(
            f"[최신자료: {mentor_doc.get('digest_title', mentor_doc.get('filename', '자료'))}]\n"
            f"요약: {mentor_doc.get('digest_summary', '')}"
        )

    # 기초 자료 검색
    basic_results = search_mentor_basic_vectorstore(mentor_id, message, k=3)
    basic_docs = []
    basic_seen: set[str] = set()
    for result in basic_results:
        doc_id = result.get("mentor_basic_doc_id", "")
        if doc_id in basic_seen:
            continue
        basic_doc = store.get_mentor_basic_doc(doc_id)
        if not basic_doc:
            continue
        basic_seen.add(doc_id)
        basic_docs.append(basic_doc)
        lines.append(
            f"[기초자료: {basic_doc.get('digest_title', basic_doc.get('filename', '자료'))}]\n"
            f"요약: {basic_doc.get('digest_summary', '')}"
        )

    ctx = "\n\n".join(lines) if lines else "(유사한 멘토 전용 자료 없음)"
    return ctx, latest_docs, basic_docs


# ── LLM 기반 큐레이션 의도 분석 프롬프트 ───────────────────
CURATION_INTENT_PROMPT = """\
사용자의 메시지를 분석하여 큐레이션 검색 의도를 추출하세요.

[큐레이션 카테고리]
- 채용정보: 채용, 취업, 구직, 면접, 이력서, 공채, 입사, 일자리, 회사, 기업 등
- IT뉴스: IT 소식, 기술 뉴스, 업계 동향, 이슈, 신기술 등
- AI타임스: AI, 인공지능, 머신러닝, 딥러닝, LLM, GPT, 생성AI 등
- 자격증·공모전: 자격증, 시험, 공모전, 해커톤, 대회, SQLD, 정보처리 등
- 개발트렌드: 개발 트렌드, 프레임워크, 기술스택, 프로그래밍 언어, 신기술 등

반드시 아래 JSON으로만 응답:
{
  "is_curation_query": true/false,
  "search_query": "벡터 검색에 사용할 자연어 쿼리 (의미적으로 풍부하게)",
  "category_hint": "카테고리명 또는 null",
  "time_range": "today|this_week|last_week|recent|all|null"
}
"""


# ── 벡터 유사도 기반 큐레이션 검색 ────────────────────────
async def _search_curations_semantic(message: str, llm: LLMProvider) -> tuple[str, list[dict]]:
    """LLM 의도 분석 + FAISS 벡터 검색으로 큐레이션 콘텐츠를 찾는다."""
    items = store.curation_items
    if not items:
        return "(큐레이션 콘텐츠가 아직 없습니다.)", []

    # 1) LLM으로 사용자 의도 분석
    try:
        intent = await llm.chat_json(CURATION_INTENT_PROMPT, message)
    except Exception:
        intent = {"is_curation_query": True, "search_query": message, "category_hint": None, "time_range": "recent"}

    is_curation = intent.get("is_curation_query", False)
    search_query = intent.get("search_query", message)
    category_hint = intent.get("category_hint")
    time_range = intent.get("time_range", "recent")

    # 2) FAISS 벡터 유사도 검색
    vector_results = search_curation_vectorstore(search_query, k=8)

    # 3) 시간 범위 필터
    now = datetime.now(_KST)
    if time_range == "today":
        cutoff = now.strftime("%Y-%m-%d")
        vector_results = [r for r in vector_results if r.get("date", "") == cutoff]
    elif time_range == "this_week":
        start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        vector_results = [r for r in vector_results if r.get("date", "") >= start]
    elif time_range == "last_week":
        start = (now - timedelta(days=now.weekday() + 7)).strftime("%Y-%m-%d")
        end = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        vector_results = [r for r in vector_results if start <= r.get("date", "") < end]
    elif time_range == "recent":
        cutoff = (now - timedelta(weeks=4)).strftime("%Y-%m-%d")
        vector_results = [r for r in vector_results if r.get("date", "") >= cutoff]

    # 4) 카테고리 힌트가 있으면 해당 카테고리 우선 정렬
    if category_hint:
        vector_results.sort(key=lambda r: (0 if r.get("category") == category_hint else 1, r.get("score", 999)))

    # 5) 벡터 결과가 부족하면 최근 3일 폴백
    if not vector_results:
        three_days_ago = (now - timedelta(days=3)).strftime("%Y-%m-%d")
        fallback = [i for i in items if i["date"] >= three_days_ago][:5]
        if not fallback:
            return "(관련 큐레이션 콘텐츠를 찾을 수 없습니다.)", []
        lines = []
        for it in fallback:
            lines.append(
                f"[{it['date']} {it['category']}] {it['title']}\n"
                f"  요약: {it['summary']}\n"
                f"  내용: {it['content'][:400]}"
            )
        return "\n\n".join(lines), fallback

    # 상위 결과를 텍스트로 포매팅
    matched_items = []
    lines = []
    for r in vector_results[:6]:
        cid = r.get("curation_id", "")
        item = next((i for i in items if i["id"] == cid), None)
        if item:
            matched_items.append(item)
            lines.append(
                f"[{item['date']} {item['category']}] {item['title']}\n"
                f"  요약: {item['summary']}\n"
                f"  내용: {item['content'][:400]}"
            )

    if not lines:
        return "(관련 큐레이션 콘텐츠를 찾을 수 없습니다.)", []

    return "\n\n".join(lines), matched_items


# ── Agent A 메인 핸들러 ──────────────────────────────────
async def handle_agent_a(
    message: str,
    retriever,
    llm: LLMProvider,
    user_id: str | None = None,
) -> dict:
    # RAG 컨텍스트
    rag_ctx = ""
    if retriever:
        docs = retriever.invoke(message[:800])
        rag_ctx = "\n\n".join(d.page_content for d in docs)

    curation_ctx, curation_matched = await _search_curations_semantic(message, llm)
    mentor_material_ctx, mentor_materials, basic_materials = _search_mentor_materials(user_id, message)

    prompt = AGENT_A_PROMPT.format(
        context=rag_ctx
        or "(지식 베이스가 비어 있습니다. 일반 KDT 지식으로 답변하세요.)",
        curation=curation_ctx,
        mentor_materials=mentor_material_ctx,
    )

    try:
        result = await llm.chat_json(prompt, message)
    except Exception:
        result = {
            "content": "죄송합니다, 일시적인 오류가 발생했습니다.",
            "choices": [],
            "needs_handoff": False,
            "related_docs": [],
            "curation_refs": [],
            "mentor_doc_refs": [],
        }

    # 이벤트 기록
    if user_id and result.get("curation_refs"):
        store.add_event(
            user_id,
            {
                "timestamp": datetime.now(_KST).isoformat(timespec="seconds"),
                "event_type": "curation_view",
                "content": f"큐레이션 조회: {', '.join(result['curation_refs'][:3])}",
                "detail": message[:60],
            },
        )

    # 벡터 검색으로 매칭된 큐레이션 아이템을 프론트엔드로 전달
    if curation_matched:
        result["curation_items"] = [
            {
                "id": it["id"],
                "title": it["title"],
                "category": it["category"],
                "date": it["date"],
                "summary": it.get("summary", ""),
                "attachment_url": it.get("attachment_url") or f"/api/curation/assets/{it['id']}",
            }
            for it in curation_matched[:5]
        ]

    if mentor_materials:
        result["related_materials"] = [
            {
                "id": doc["id"],
                "digest_title": doc.get("digest_title", doc.get("filename", "자료")),
                "digest_summary": doc.get("digest_summary", ""),
                "attachment_url": (
                    doc.get("source_url")
                    if doc.get("source_kind") == "link"
                    else f"/api/mentor/knowledge/assets/{doc['id']}"
                ),
                "source_kind": doc.get("source_kind", "file"),
                "doc_type": "latest",
            }
            for doc in mentor_materials[:3]
        ]

    if basic_materials:
        basics = [
            {
                "id": doc["id"],
                "digest_title": doc.get("digest_title", doc.get("filename", "자료")),
                "digest_summary": doc.get("digest_summary", ""),
                "attachment_url": (
                    doc.get("source_url")
                    if doc.get("source_kind") == "link"
                    else f"/api/mentor/basic/assets/{doc['id']}"
                ),
                "source_kind": doc.get("source_kind", "file"),
                "doc_type": "basic",
            }
            for doc in basic_materials[:3]
        ]
        result.setdefault("related_materials", []).extend(basics)

    return result
