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
You are "Agent A — Administrative & Career Mentor" for a Korean government-funded (KDT) coding bootcamp.
Your role is to answer questions about bootcamp administration, job searching, certifications, competitions, and bootcamp regulations.
ALL of your responses MUST be written in Korean (한국어).

[Knowledge Base Context]
{context}

[Curation Data — curated job postings, IT news, AI news, certifications, competitions, dev trends]
{curation}

[Mentor-Uploaded Materials — learning resources shared by the student's assigned mentor]
{mentor_materials}

[Response Rules]
1. If the question is vague or broad, provide 3–4 specific actionable choices so the student can narrow down their intent.
2. For specific questions, give a direct, concise answer. If relevant documents or materials exist in the context above, reference them.
3. When the student asks about curated content (job postings, IT news, AI news, etc.), use the curation data provided. If the requested item is missing, clearly state the date and topic so the student knows what to look for.
4. If the student appears to need emotional support or deep counseling, set needs_handoff to true and gently suggest connecting with their mentor.
5. Keep answers concise yet informative. Use bullet points or short paragraphs. Avoid overly long responses.
6. When mentor materials are relevant, mention them naturally in your answer so the student knows they can view or download them.

IMPORTANT: Respond ONLY with the JSON below. Write ALL text values in Korean. Do NOT include any other text outside the JSON.
{{
  "content": "Your answer message in Korean",
  "choices": [
    {{"label": "Choice title in Korean", "description": "Short description in Korean"}}
  ],
  "needs_handoff": false,
  "related_docs": ["Referenced document names"],
  "curation_refs": ["Referenced curation IDs"],
  "mentor_doc_refs": ["Referenced mentor document IDs"]
}}

- Set choices to an empty array [] when no choices are needed.
- Set needs_handoff to true only when emotional counseling is needed.
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


# ── LLM-based curation intent analysis ───────────────────
CURATION_INTENT_PROMPT = """\
Analyze the user's message to determine if they are searching for curated content, and extract search parameters.
The user writes in Korean. You must understand Korean intent and produce the JSON output below.

[Available Curation Categories]
- 채용정보 (Job Postings): hiring, employment, job search, interviews, resumes, recruitment, companies
- IT뉴스 (IT News): IT industry news, tech trends, industry developments, new technologies
- AI타임스 (AI Times): AI, artificial intelligence, machine learning, deep learning, LLM, GPT, generative AI
- 자격증·공모전 (Certifications & Competitions): certifications, exams, hackathons, competitions, SQLD, information processing
- 개발트렌드 (Dev Trends): development trends, frameworks, tech stacks, programming languages, emerging tech

IMPORTANT: Respond ONLY with the JSON below. Do NOT include any other text.
{
  "is_curation_query": true or false,
  "search_query": "A semantically rich natural-language query in Korean for vector similarity search",
  "category_hint": "Category name in Korean (e.g. '채용정보') or null if uncertain",
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
                "timestamp": datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S"),
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
