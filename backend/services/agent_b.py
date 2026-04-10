"""
Agent B — 조교 스케줄러 & 통역기.
빈 시간대 예약 안내 · 수강생의 모호한 요청을 전문 브리핑 리포트로 변환.
"""

import logging
import re
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

BOOKING_NORMALIZE_PROMPT = """\
당신은 조교 보충수업 접수 비서입니다.
학생이 보낸 이름, 연락처, 요청 내용을 조교 대시보드에 표시하기 좋게 짧고 명확하게 정리하세요.

반드시 아래 JSON 형식으로만 답변하세요:
{
  "student_name": "학생 이름",
  "student_phone": "010-1234-5678",
  "cleaned_request": "조교가 바로 이해할 수 있는 정리된 요청",
  "short_summary": "대시보드용 한 줄 요약"
}

규칙:
- 이름과 연락처는 입력값을 기반으로만 정리하고, 없는 값은 비워두세요.
- 연락처는 가능한 경우 010-1234-5678 형식으로 맞추세요.
- 요청 내용은 학생 말투를 유지하되 조교가 보기 좋게 1~2문장으로 정리하세요.
- short_summary 는 40자 이내의 짧은 요약으로 만드세요.
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


_BOOKING_KEYWORDS = ["예약", "보충수업", "보충 수업", "조교 연결", "조교 예약", "시간대"]

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


async def handle_agent_b(
    message: str,
    llm: LLMProvider,
    user_id: str | None = None,
) -> dict:
    # ── 예약 요청 감지 → 날짜 선택지 먼저 반환 ──
    is_booking = any(kw in message for kw in _BOOKING_KEYWORDS)
    if is_booking:
        slots = store.get_available_slots()
        if not slots:
            return {
                "content": "현재 예약 가능한 시간이 없습니다.\n조교 선생님이 일정을 등록하면 안내해 드릴게요.",
                "choices": [],
                "needs_handoff": False,
                "suggest_booking": False,
            }
        # 날짜별 그룹핑
        date_map: dict[str, int] = {}
        for s in slots:
            d = s["date"]
            date_map[d] = date_map.get(d, 0) + 1
        choices = []
        for d in sorted(date_map):
            wd = WEEKDAY_KR[datetime.strptime(d, "%Y-%m-%d").weekday()]
            choices.append({
                "label": f"{d} ({wd})",
                "description": f"{date_map[d]}개 시간대 가능",
                "_action": "pick_date",
                "_date": d,
            })
        return {
            "content": "조교 보충수업 예약을 도와드리겠습니다.\n원하시는 날짜를 선택해 주세요.",
            "choices": choices,
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
