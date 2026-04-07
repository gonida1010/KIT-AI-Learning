"""
카카오 i 오픈빌더 Webhook — 스킬 서버 엔드포인트.
카카오톡 채널로 들어온 메시지를 처리하고, 카카오 SkillResponse 형식으로 응답.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Request

from db.store import store
from services.ai_chat import generate_chat_response

router = APIRouter(prefix="/api/kakao", tags=["kakao"])
logger = logging.getLogger(__name__)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex[:12]


# ─── 카카오 SkillResponse 빌더 ──────────────────────────────

def simple_text(text: str) -> dict:
    """SimpleText 응답."""
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ]
        }
    }


def text_with_quick_replies(text: str, choices: list[dict], show_handoff: bool = True) -> dict:
    """텍스트 + 선택지 QuickReply 응답."""
    quick_replies = []
    for c in choices:
        quick_replies.append({
            "messageText": c.get("label", ""),
            "action": "message",
            "label": c.get("label", ""),
        })

    if show_handoff:
        quick_replies.append({
            "messageText": "멘토님과 직접 상담하기",
            "action": "message",
            "label": "🙋‍♂️ 멘토 상담 요청",
        })

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ],
            "quickReplies": quick_replies
        }
    }


def handoff_response() -> dict:
    """멘토 상담 대기열 등록 안내."""
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": (
                            "✅ 멘토 상담 대기열에 등록되었습니다.\n\n"
                            "담당 멘토님이 최대한 빠르게 연락드리겠습니다.\n"
                            "심야·주말에는 다음 영업일 오전에 확인됩니다."
                        )
                    }
                }
            ]
        }
    }


# ─── 카카오 Webhook 엔드포인트 ─────────────────────────────

@router.post("/webhook")
async def kakao_webhook(request: Request):
    """
    카카오 i 오픈빌더 스킬 서버 메인 엔드포인트.
    POST body: 카카오 SkillPayload JSON
    """
    from main import retriever, llm

    body = await request.json()
    logger.info(f"카카오 웹훅 수신: {body}")

    # 카카오 페이로드에서 사용자 정보와 메시지 추출
    user_request = body.get("userRequest", {})
    utterance = user_request.get("utterance", "").strip()
    kakao_user_id = user_request.get("user", {}).get("id", "unknown")

    # 블록 정보 (오픈빌더에서 설정한 블록 이름으로 분기 가능)
    block_name = user_request.get("block", {}).get("name", "")

    if not utterance:
        return simple_text("메시지를 입력해 주세요.")

    # ── 학생 자동 등록 ──
    student_id = f"kakao_{kakao_user_id}"
    if not store.get_student(student_id):
        store.students[student_id] = {
            "id": student_id,
            "name": f"카카오 유저 ({kakao_user_id[:8]})",
        }
        store._save()

    # ── 멘토 상담 요청 감지 ──
    if utterance in ("멘토님과 직접 상담하기", "멘토 상담 요청"):
        last_msgs = store.get_conversation(student_id)
        last_user_msg = ""
        for m in reversed(last_msgs):
            if m.get("role") == "user":
                last_user_msg = m["content"]
                break

        store.add_handoff({
            "id": _uid(),
            "student_id": student_id,
            "student_name": store.get_student(student_id).get("name", ""),
            "reason": "카카오톡 멘토 상담 요청",
            "last_message": last_user_msg or utterance,
            "priority": "medium",
            "status": "pending",
            "created_at": _now(),
        })

        store.add_event(student_id, {
            "timestamp": _now(),
            "event_type": "handoff",
            "content": "멘토 상담 요청",
            "detail": last_user_msg[:80] if last_user_msg else utterance[:80],
        })

        return handoff_response()

    # ── 사용자 메시지 저장 ──
    store.add_message(student_id, {
        "id": _uid(), "student_id": student_id, "role": "user",
        "content": utterance, "choices": None, "has_handoff": False,
        "timestamp": _now(),
    })

    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": utterance[:60], "detail": "카카오톡 대화",
    })

    # ── AI 응답 생성 ──
    ai_result = await generate_chat_response(utterance, retriever, llm)

    content = ai_result.get("content", "죄송합니다, 일시적인 오류가 발생했습니다.")
    choices = ai_result.get("choices", [])
    needs_handoff = ai_result.get("needs_handoff", False)

    # AI 응답 저장
    store.add_message(student_id, {
        "id": _uid(), "student_id": student_id, "role": "assistant",
        "content": content, "choices": choices or None, "has_handoff": True,
        "timestamp": _now(),
    })

    # ── 감정적 상담 필요 시 자동으로 우선순위 높은 핸드오프 등록 ──
    if needs_handoff:
        store.add_handoff({
            "id": _uid(),
            "student_id": student_id,
            "student_name": store.get_student(student_id).get("name", ""),
            "reason": "AI 감정 상담 필요 감지",
            "last_message": utterance,
            "priority": "high",
            "status": "pending",
            "created_at": _now(),
        })

    # ── 선택지가 있으면 QuickReply, 없으면 SimpleText ──
    if choices and len(choices) > 0:
        return text_with_quick_replies(content, choices, show_handoff=True)
    else:
        # 선택지 없어도 항상 멘토 상담 버튼 추가
        return text_with_quick_replies(content, [], show_handoff=True)


@router.post("/webhook/schedule")
async def kakao_schedule_webhook(request: Request):
    """
    조교 예약 전용 스킬 블록.
    수강생이 카카오톡에서 보충 수업을 요청할 때 사용.
    """
    body = await request.json()
    user_request = body.get("userRequest", {})
    utterance = user_request.get("utterance", "").strip()
    kakao_user_id = user_request.get("user", {}).get("id", "unknown")

    # 조교 빈 시간 조회
    available = store.get_available_slots()

    if not available:
        return simple_text(
            "현재 예약 가능한 조교 시간이 없습니다.\n"
            "관리자 페이지에서 조교 스케줄을 확인해 주세요."
        )

    lines = ["📅 예약 가능한 보충 수업 시간:\n"]
    for i, slot in enumerate(available[:5], 1):
        lines.append(
            f"{i}. {slot['ta_name']} | {slot['date']} {slot['start_time']}~{slot['end_time']}"
        )
    lines.append("\n원하는 시간의 번호와 어려운 내용을 함께 입력해 주세요.")
    lines.append("예: \"1번 파이썬 클래스에서 self가 뭔지 모르겠어요\"")

    return simple_text("\n".join(lines))
