"""
웹 챗봇 API — 멀티 에이전트 라우팅.
단일 창구 → Main Router AI → Agent A / Agent B / Human Handoff.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.store import store

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex[:12]


class ChatRequest(BaseModel):
    message: str
    student_id: str | None = None
    token: str | None = None


class HandoffWebRequest(BaseModel):
    student_id: str


@router.post("")
async def chat(req: ChatRequest):
    from main import retriever, llm_provider
    from services.agent_router import classify_intent
    from services.agent_a import handle_agent_a
    from services.agent_b import handle_agent_b

    if not req.message.strip():
        raise HTTPException(400, "메시지를 입력해 주세요.")

    # 토큰 → student_id 해소
    sid = req.student_id
    if not sid and req.token:
        sid = store.get_session(req.token)
    if not sid:
        sid = "student_001"

    # 학생 자동 등록
    if not store.get_user(sid):
        store.create_user({
            "id": sid, "kakao_id": None,
            "name": f"웹 유저 ({sid[:8]})",
            "profile_image": "", "role": "student",
            "mentor_id": None, "invite_code": None,
            "career_pref": None, "created_at": _now(),
        })

    # 사용자 메시지 저장
    user_msg = {
        "id": _uid(), "user_id": sid, "channel": "web",
        "role": "user", "agent_type": None,
        "content": req.message, "choices": None, "metadata": None,
        "created_at": _now(),
    }
    store.add_message(sid, user_msg)
    store.add_event(sid, {
        "timestamp": _now(), "event_type": "chat",
        "content": req.message[:60], "detail": "웹 챗봇 대화",
    })

    # ── 멀티 에이전트 라우팅 ──
    routing = await classify_intent(req.message, llm_provider)
    intent = routing["intent"]
    agent_type = intent

    if intent == "human_handoff":
        # 멘토 핸드오프
        student = store.get_user(sid)
        store.add_handoff({
            "id": _uid(), "student_id": sid,
            "student_name": student.get("name", "") if student else "",
            "reason": "AI 감정 상담 필요 감지",
            "last_message": req.message,
            "priority": "high", "status": "pending", "created_at": _now(),
        })
        content = (
            "말씀하신 내용을 멘토님께 전달했습니다. 😊\n"
            "담당 멘토님이 최대한 빠르게 연락드리겠습니다.\n"
            "혼자 고민하지 마시고 편하게 기다려 주세요."
        )
        ai_result = {"content": content, "choices": [], "needs_handoff": True}
    elif intent == "agent_b":
        ai_result = await handle_agent_b(req.message, llm_provider, sid)
    else:
        ai_result = await handle_agent_a(req.message, retriever, llm_provider, sid)

    content = ai_result.get("content", "죄송합니다, 오류가 발생했습니다.")
    choices = ai_result.get("choices", [])
    curation_items = ai_result.get("curation_items", [])
    needs_handoff = ai_result.get("needs_handoff", False)

    assistant_msg = {
        "id": _uid(), "user_id": sid, "channel": "web",
        "role": "assistant", "agent_type": agent_type,
        "content": content, "choices": choices or None,
        "metadata": {
            "routing": routing,
            "curation_items": curation_items,
            "related_materials": ai_result.get("related_materials", []),
        },
        "created_at": _now(),
    }
    store.add_message(sid, assistant_msg)

    # Agent A 응답 중 멘토 핸드오프 필요 감지
    if needs_handoff and intent != "human_handoff":
        student = store.get_user(sid)
        store.add_handoff({
            "id": _uid(), "student_id": sid,
            "student_name": student.get("name", "") if student else "",
            "reason": "AI 감정 상담 필요 감지 (웹)",
            "last_message": req.message,
            "priority": "high", "status": "pending", "created_at": _now(),
        })

    return {
        "reply": content,
        "choices": choices,
        "curation_items": curation_items,
        "related_materials": ai_result.get("related_materials", []),
        "needs_handoff": needs_handoff,
        "agent_type": agent_type,
    }


@router.get("/history/{student_id}")
async def chat_history(student_id: str):
    return store.get_conversation(student_id)


@router.post("/handoff")
async def request_handoff(req: HandoffWebRequest):
    student = store.get_user(req.student_id)
    if not student:
        raise HTTPException(404, "학생을 찾을 수 없습니다.")
    last_msgs = store.get_conversation(req.student_id)
    last_user_msg = ""
    for m in reversed(last_msgs):
        if m.get("role") == "user":
            last_user_msg = m["content"]
            break
    store.add_handoff({
        "id": _uid(), "student_id": req.student_id,
        "student_name": student.get("name", ""),
        "reason": "웹 챗봇 멘토 상담 요청",
        "last_message": last_user_msg or "(대화 없음)",
        "priority": "medium", "status": "pending", "created_at": _now(),
    })
    store.add_event(req.student_id, {
        "timestamp": _now(), "event_type": "handoff",
        "content": "멘토 상담 요청 (웹)", "detail": last_user_msg[:80],
    })
    return {"status": "ok", "message": "멘토 상담 대기열에 등록되었습니다."}
