"""
Agent B — 조교 스케줄러 & 통역기.
빈 시간대 예약 안내 · 수강생의 모호한 요청을 전문 브리핑 리포트로 변환.
"""

import logging
from datetime import datetime

from services.llm_provider import LLMProvider
from db.store import store

logger = logging.getLogger(__name__)

# ── Agent B 응답 프롬프트 ────────────────────────────────
AGENT_B_PROMPT = """\
당신은 국비지원(KDT) 코딩 학원의 'Agent B — 조교 스케줄러 & 통역기'입니다.
수강생의 학습 질문에 답변하고, 필요시 조교 보충수업 예약을 안내합니다.

[예약 가능 시간]
{slots}

[응답 규칙]
1. 프로그래밍 질문에는 간결하게 답변 + 조교 보충수업 안내.
2. 예약 요청 시 가능한 시간대를 선택지로 제시.
3. 모호한 표현(예: "별표 나오는 거 모르겠어요")을 전문 용어로 번역.
4. 코드 질문에는 핵심 개념을 짚어주세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "content": "답변 메시지 텍스트",
  "choices": [
    {{"label": "선택지 제목", "description": "설명"}}
  ],
  "needs_handoff": false,
  "suggest_booking": true,
  "translated_query": "수강생 요청을 전문 용어로 번역한 버전"
}}
"""

# ── 브리핑 리포트 생성 프롬프트 ──────────────────────────
BRIEFING_PROMPT = """\
당신은 국비지원 코딩 학원의 AI 학습 분석 어시스턴트입니다.
수강생의 보충 수업 요청과 이력을 분석하여 조교(TA)에게 전달할 브리핑 리포트를 생성합니다.

[수강생 정보]
이름: {student_name}
최근 활동 이력: {search_history}

[수강생 원본 요청]
"{raw_input}"

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "student_name": "{student_name}",
  "search_history": "최근 활동 키워드 요약",
  "core_need": "핵심 학습 필요 주제",
  "ai_recommendation": "AI 추천 지도 방향 (2~3문장)"
}}
"""


def _slots_text() -> str:
    slots = store.get_available_slots()
    if not slots:
        return "(현재 예약 가능한 시간이 없습니다.)"
    lines = []
    for i, s in enumerate(slots[:8], 1):
        lines.append(
            f"{i}. {s['ta_name']} | {s['date']} {s['start_time']}~{s['end_time']}"
        )
    return "\n".join(lines)


async def handle_agent_b(
    message: str,
    llm: LLMProvider,
    user_id: str | None = None,
) -> dict:
    prompt = AGENT_B_PROMPT.format(slots=_slots_text())
    try:
        result = await llm.chat_json(prompt, message)
    except Exception:
        result = {
            "content": "죄송합니다, 일시적인 오류가 발생했습니다.",
            "choices": [],
            "needs_handoff": False,
            "suggest_booking": False,
            "translated_query": "",
        }
    return result


async def generate_briefing_report(
    student_name: str,
    raw_input: str,
    search_history: list[str],
    llm: LLMProvider,
) -> dict:
    history_str = ", ".join(search_history) if search_history else "이력 없음"
    prompt = BRIEFING_PROMPT.format(
        student_name=student_name,
        search_history=history_str,
        raw_input=raw_input,
    )
    try:
        return await llm.chat_json(prompt, raw_input)
    except Exception:
        return {
            "student_name": student_name,
            "search_history": history_str,
            "core_need": raw_input,
            "ai_recommendation": "AI 분석 실패. 수강생 원본 요청을 참고해 주세요.",
        }
