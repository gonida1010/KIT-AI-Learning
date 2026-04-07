"""
웹 사이트 챗봇 API — 카카오톡과 동일한 AI 기능을 웹에서도 제공.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.store import store
from services.ai_chat import generate_chat_response

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex[:12]


class ChatRequest(BaseModel):
    student_id: str = "student_1"
    message: str


class HandoffWebRequest(BaseModel):
    student_id: str


@router.post("")
async def chat(req: ChatRequest):
    """웹 챗봇 메시지 → AI 응답."""
    from main import retriever, llm

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해 주세요.")

    student = store.get_student(req.student_id)
    if not student:
        # 자동 등록
        store.students[req.student_id] = {
            "id": req.student_id,
            "name": f"웹 유저 ({req.student_id[:8]})",
        }
        store._save()

    # 사용자 메시지 저장
    user_msg = {
        "id": _uid(), "student_id": req.student_id, "role": "user",
        "content": req.message, "choices": None, "has_handoff": False,
        "timestamp": _now(),
    }
    store.add_message(req.student_id, user_msg)
    store.add_event(req.student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": req.message[:60], "detail": "웹 챗봇 대화",
    })

    # AI 응답
    ai_result = await generate_chat_response(req.message, retriever, llm)

    content = ai_result.get("content", "죄송합니다, 일시적인 오류가 발생했습니다.")
    choices = ai_result.get("choices", [])
    needs_handoff = ai_result.get("needs_handoff", False)
    related_docs = ai_result.get("related_docs", [])

    assistant_msg = {
        "id": _uid(), "student_id": req.student_id, "role": "assistant",
        "content": content, "choices": choices or None, "has_handoff": True,
        "timestamp": _now(),
    }
    store.add_message(req.student_id, assistant_msg)

    # 감정 상담 필요 시 자동 핸드오프
    if needs_handoff:
        store.add_handoff({
            "id": _uid(),
            "student_id": req.student_id,
            "student_name": store.get_student(req.student_id).get("name", ""),
            "reason": "AI 감정 상담 필요 감지 (웹)",
            "last_message": req.message,
            "priority": "high",
            "status": "pending",
            "created_at": _now(),
        })

    return {
        "reply": assistant_msg,
        "choices": choices,
        "needs_handoff": needs_handoff,
        "related_docs": related_docs,
    }


@router.get("/history/{student_id}")
async def chat_history(student_id: str):
    """대화 이력 조회."""
    return store.get_conversation(student_id)


@router.post("/handoff")
async def request_handoff(req: HandoffWebRequest):
    """웹에서 멘토 직접 상담 요청."""
    student = store.get_student(req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    last_msgs = store.get_conversation(req.student_id)
    last_user_msg = ""
    for m in reversed(last_msgs):
        if m.get("role") == "user":
            last_user_msg = m["content"]
            break

    store.add_handoff({
        "id": _uid(),
        "student_id": req.student_id,
        "student_name": student.get("name", ""),
        "reason": "웹 챗봇 멘토 상담 요청",
        "last_message": last_user_msg or "(대화 내역 없음)",
        "priority": "medium",
        "status": "pending",
        "created_at": _now(),
    })

    store.add_event(req.student_id, {
        "timestamp": _now(),
        "event_type": "handoff",
        "content": "멘토 상담 요청 (웹)",
        "detail": last_user_msg[:80] if last_user_msg else "",
    })

    return {"status": "ok", "message": "멘토 상담 대기열에 등록되었습니다."}
