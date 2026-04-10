"""
Agent B — 조교 스케줄러 & 통역기.
빈 시간대 예약 안내 · 수강생의 모호한 요청을 전문 브리핑 리포트로 변환.
"""

import logging
import re

from services.llm_provider import LLMProvider
from db.store import store

logger = logging.getLogger(__name__)

# ── Agent B response prompt ──────────────────────────────
AGENT_B_PROMPT = """\
You are "Agent B — TA Scheduler & Learning Interpreter" for a Korean government-funded (KDT) coding bootcamp.
Your role is to answer programming/technical questions and guide students to book supplementary TA sessions when needed.
ALL of your responses MUST be written in Korean (한국어).

[Currently Available TA Time Slots]
{slots}

[Response Rules]
1. For programming or technical questions, provide a concise and accurate explanation of the core concept, then suggest booking a TA session for deeper hands-on practice if appropriate.
2. When the student asks to book a session, present available time slots as selectable choices.
3. Translate vague or colloquial expressions into proper technical terminology. For example, "별표 나오는 거" → "Python 언패킹 연산자(asterisk / *args, **kwargs)".
4. For code-related questions, pinpoint the key concept or common mistake and explain it clearly.
5. Keep answers practical and beginner-friendly. Avoid overwhelming the student with too much detail.

IMPORTANT: Respond ONLY with the JSON below. Write ALL text values in Korean. Do NOT include any other text outside the JSON.
{{
  "content": "Your answer message in Korean",
  "choices": [
    {{"label": "Choice title in Korean", "description": "Short description in Korean"}}
  ],
  "needs_handoff": false,
  "suggest_booking": true,
  "translated_query": "Student's request translated into proper technical terminology in Korean"
}}
"""

# ── Briefing report generation prompt ────────────────────
BRIEFING_PROMPT = """\
You are an AI learning analytics assistant for a Korean coding bootcamp.
Analyze the student's supplementary lesson request and their recent activity to generate a concise briefing report for the teaching assistant (TA).
The TA will use this report to prepare for the session. ALL output text MUST be in Korean (한국어).

[Student Information]
Name: {student_name}
Recent Activity History: {search_history}

[Student's Original Request]
"{raw_input}"

[Instructions]
- Identify the core topic the student needs help with based on their request and history.
- Summarize their recent activity into key learning themes or weak areas.
- Provide a practical recommendation (2–3 sentences) for how the TA should approach the session.

IMPORTANT: Respond ONLY with the JSON below. Write ALL text values in Korean.
{{
  "student_name": "{student_name}",
  "search_history": "Summary of recent activity keywords in Korean",
  "core_need": "Core learning topic the student needs help with in Korean",
  "ai_recommendation": "AI-recommended teaching approach in Korean (2–3 sentences)"
}}
"""

BOOKING_NORMALIZE_PROMPT = """\
You are a booking intake assistant for a coding bootcamp's TA supplementary lesson system.
Clean up and normalize the student's booking request so it displays neatly on the TA dashboard.
ALL output text MUST be in Korean (한국어).

Respond ONLY with the JSON below:
{
  "student_name": "Student's name (from input, keep as-is)",
  "student_phone": "Phone in 010-1234-5678 format if possible",
  "cleaned_request": "Cleaned version of the request that a TA can immediately understand, in Korean, 1–2 sentences",
  "short_summary": "Dashboard one-liner summary in Korean, max 40 characters"
}

Rules:
- Only use information provided in the input. Do NOT fabricate names or phone numbers.
- Format phone numbers as 010-1234-5678 when possible. Leave blank if not provided.
- Preserve the student's intent but make it readable and professional for the TA.
- The short_summary must be ≤ 40 Korean characters.
"""


def _format_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return (phone or "").strip()


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


_BOOKING_KEYWORDS = ["예약", "보충수업", "보충 수업", "조교 연결", "조교 예약", "시간대", "취소"]


async def handle_agent_b(
    message: str,
    llm: LLMProvider,
    user_id: str | None = None,
) -> dict:
    # ── 예약 요청 감지 → 예약/취소 선택지 먼저 반환 ──
    is_booking = any(kw in message for kw in _BOOKING_KEYWORDS)
    if is_booking:
        return {
            "content": "조교 보충수업을 도와드리겠습니다.\n원하시는 메뉴를 선택해 주세요.",
            "choices": [
                {"label": "예약하기", "description": "조교 보충수업 새로 예약", "_action": "booking_new"},
                {"label": "취소하기", "description": "기존 예약 취소", "_action": "booking_cancel"},
            ],
            "needs_handoff": False,
            "suggest_booking": True,
        }

    # ── 일반 학습 질문 → LLM 응답 ──
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


async def normalize_booking_request(
    student_name: str,
    student_phone: str,
    raw_input: str,
    llm: LLMProvider | None,
) -> dict:
    payload = (
        f"이름: {student_name.strip()}\n"
        f"연락처: {student_phone.strip()}\n"
        f"요청 내용: {raw_input.strip()}"
    )

    if llm:
        try:
            result = await llm.chat_json(BOOKING_NORMALIZE_PROMPT, payload)
            cleaned_request = (result.get("cleaned_request") or raw_input).strip()
            short_summary = (result.get("short_summary") or cleaned_request).strip()
            return {
                "student_name": (result.get("student_name") or student_name).strip(),
                "student_phone": _format_phone(result.get("student_phone") or student_phone),
                "cleaned_request": cleaned_request,
                "short_summary": short_summary[:40],
            }
        except Exception:
            logger.exception("예약 접수 정리 실패")

    cleaned_request = (raw_input or "").strip()
    return {
        "student_name": student_name.strip(),
        "student_phone": _format_phone(student_phone),
        "cleaned_request": cleaned_request,
        "short_summary": cleaned_request[:40],
    }
