"""
카카오 i 오픈빌더 Webhook — 스킬 서버.
단일 창구 → Main Router AI → Agent A / Agent B / Human Handoff.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Request

from db.store import store

router = APIRouter(prefix="/api/kakao", tags=["kakao"])
logger = logging.getLogger(__name__)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex[:12]


# ── SkillResponse 빌더 ──────────────────────────────────
def simple_text(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text}}]}}


def text_with_quick_replies(text: str, choices: list[dict], show_handoff: bool = True) -> dict:
    qr = []
    for c in choices:
        qr.append({"messageText": c.get("label", ""), "action": "message", "label": c.get("label", "")})
    if show_handoff:
        qr.append({"messageText": "멘토님과 직접 상담하기", "action": "message", "label": "🙋‍♂️ 멘토 상담 요청"})
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text}}], "quickReplies": qr}}


# ── 메인 웹훅 ────────────────────────────────────────────
@router.post("/webhook")
async def kakao_webhook(request: Request):
    from main import retriever, llm_provider
    from services.agent_router import classify_intent
    from services.agent_a import handle_agent_a
    from services.agent_b import handle_agent_b

    body = await request.json()
    logger.info(f"카카오 웹훅: {body}")

    user_request = body.get("userRequest", {})
    utterance = user_request.get("utterance", "").strip()
    kakao_user_id = user_request.get("user", {}).get("id", "unknown")

    if not utterance:
        return simple_text("메시지를 입력해 주세요.")

    student_id = f"kakao_{kakao_user_id}"
    if not store.get_user(student_id):
        store.create_user({
            "id": student_id, "kakao_id": kakao_user_id,
            "name": f"카카오 유저 ({kakao_user_id[:8]})",
            "profile_image": "", "role": "student",
            "mentor_id": None, "invite_code": None,
            "career_pref": None, "created_at": _now(),
        })

    # 멘토 상담 요청 바로가기
    if utterance in ("멘토님과 직접 상담하기", "멘토 상담 요청"):
        last_msgs = store.get_conversation(student_id)
        last_user_msg = ""
        for m in reversed(last_msgs):
            if m.get("role") == "user":
                last_user_msg = m["content"]
                break
        store.add_handoff({
            "id": _uid(), "student_id": student_id,
            "student_name": store.get_user(student_id).get("name", ""),
            "reason": "카카오톡 멘토 상담 요청",
            "last_message": last_user_msg or utterance,
            "priority": "medium", "status": "pending", "created_at": _now(),
        })
        store.add_event(student_id, {
            "timestamp": _now(), "event_type": "handoff",
            "content": "멘토 상담 요청", "detail": (last_user_msg or utterance)[:80],
        })
        return simple_text("✅ 멘토 상담 대기열에 등록되었습니다.\n담당 멘토님이 최대한 빠르게 연락드리겠습니다.")

    # 사용자 메시지 저장
    store.add_message(student_id, {
        "id": _uid(), "user_id": student_id, "channel": "kakao",
        "role": "user", "agent_type": None,
        "content": utterance, "choices": None, "metadata": None,
        "created_at": _now(),
    })
    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": utterance[:60], "detail": "카카오톡 대화",
    })

    # ── 멀티 에이전트 라우팅 ──
    routing = await classify_intent(utterance, llm_provider)
    intent = routing["intent"]

    if intent == "human_handoff":
        store.add_handoff({
            "id": _uid(), "student_id": student_id,
            "student_name": store.get_user(student_id).get("name", ""),
            "reason": "AI 감정 상담 필요 감지",
            "last_message": utterance,
            "priority": "high", "status": "pending", "created_at": _now(),
        })
        store.add_message(student_id, {
            "id": _uid(), "user_id": student_id, "channel": "kakao",
            "role": "assistant", "agent_type": "human_handoff",
            "content": "멘토 상담 대기열에 등록되었습니다.", "choices": None,
            "metadata": None, "created_at": _now(),
        })
        return simple_text(
            "말씀하신 내용을 멘토님께 전달했습니다. 😊\n"
            "담당 멘토님이 최대한 빠르게 연락드리겠습니다."
        )

    if intent == "agent_b":
        ai_result = await handle_agent_b(utterance, llm_provider, student_id)
    else:
        ai_result = await handle_agent_a(utterance, retriever, llm_provider, student_id)

    content = ai_result.get("content", "죄송합니다, 오류가 발생했습니다.")
    choices = ai_result.get("choices", [])

    store.add_message(student_id, {
        "id": _uid(), "user_id": student_id, "channel": "kakao",
        "role": "assistant", "agent_type": intent,
        "content": content, "choices": choices or None,
        "metadata": {"routing": routing}, "created_at": _now(),
    })

    if ai_result.get("needs_handoff"):
        store.add_handoff({
            "id": _uid(), "student_id": student_id,
            "student_name": store.get_user(student_id).get("name", ""),
            "reason": "AI 감정 상담 감지", "last_message": utterance,
            "priority": "high", "status": "pending", "created_at": _now(),
        })

    if choices:
        return text_with_quick_replies(content, choices)
    return text_with_quick_replies(content, [], show_handoff=True)


# ── 조교 예약 전용 블록 ──────────────────────────────────
@router.post("/webhook/schedule")
async def kakao_schedule_webhook(request: Request):
    body = await request.json()
    available = store.get_available_slots()
    if not available:
        return simple_text("현재 예약 가능한 조교 시간이 없습니다.")
    lines = ["📅 예약 가능한 보충 수업 시간:\n"]
    for i, slot in enumerate(available[:5], 1):
        lines.append(f"{i}. {slot['ta_name']} | {slot['date']} {slot['start_time']}~{slot['end_time']}")
    lines.append('\n원하는 번호와 어려운 내용을 함께 입력해 주세요.')
    return simple_text("\n".join(lines))
