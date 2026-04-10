"""
웹 챗봇 API — 멀티 에이전트 라우팅.
단일 창구 → Main Router AI → Agent A / Agent B / Human Handoff.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.store import store

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

_KST = timezone(timedelta(hours=9))


def _now():
    return datetime.now(_KST).isoformat(timespec="seconds")


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


class TipsRequest(BaseModel):
    student_id: str | None = None
    token: str | None = None
    type: str = "latest"   # "latest" | "basic"


@router.post("/tips")
async def learning_tips(req: TipsRequest):
    """학생의 담당 멘토가 올린 자료 반환. type=latest: 최신 자료, type=basic: 기초 자료."""
    sid = req.student_id
    if not sid and req.token:
        sid = store.get_session(req.token)
    if not sid:
        sid = "student_001"

    student = store.get_user(sid)
    mentor_id = student.get("mentor_id") if student else None

    mentor_docs = []
    mentor_name = ""
    if mentor_id:
        mentor = store.get_user(mentor_id)
        mentor_name = mentor.get("name", "") if mentor else ""

        if req.type == "basic":
            raw_docs = store.get_mentor_basic_docs(mentor_id)[:5]
            asset_prefix = "/api/mentor/basic/assets"
        else:
            raw_docs = store.get_mentor_docs(mentor_id)[:5]
            asset_prefix = "/api/mentor/knowledge/assets"

        for d in raw_docs:
            source_kind = d.get("source_kind", "file")
            if source_kind == "link":
                attachment_url = d.get("source_url", "")
            else:
                attachment_url = f"{asset_prefix}/{d['id']}"
            mentor_docs.append({
                "id": d.get("id"),
                "title": d.get("digest_title") or d.get("filename", ""),
                "summary": d.get("digest_summary", ""),
                "uploaded_at": d.get("uploaded_at", ""),
                "attachment_url": attachment_url,
                "source_kind": source_kind,
            })

    return {
        "mentor_name": mentor_name,
        "mentor_docs": mentor_docs,
        "type": req.type,
    }


class BookingConfirmRequest(BaseModel):
    slot_id: str
    token: str | None = None
    student_id: str | None = None
    description: str = "웹 채팅에서 예약"


@router.get("/booking/dates")
async def booking_dates():
    """예약 가능한 날짜 목록 반환 (향후 2주)."""
    slots = store.get_available_slots()
    date_map: dict[str, int] = {}
    for s in slots:
        d = s["date"]
        date_map[d] = date_map.get(d, 0) + 1
    dates = sorted(date_map.keys())
    return [{"date": d, "count": date_map[d]} for d in dates]


@router.get("/booking/slots")
async def booking_slots(date: str):
    """특정 날짜의 예약 가능 시간대 반환."""
    slots = store.get_available_slots()
    filtered = [s for s in slots if s["date"] == date]
    filtered.sort(key=lambda s: s.get("start_time", ""))
    return [
        {
            "id": s["id"],
            "ta_name": s.get("ta_name", ""),
            "start_time": s.get("start_time", ""),
            "end_time": s.get("end_time", ""),
        }
        for s in filtered
    ]


@router.post("/booking/confirm")
async def booking_confirm(req: BookingConfirmRequest):
    """웹 채팅에서 슬롯 예약 확정."""
    from main import llm_provider
    from services.agent_b import generate_briefing_report, normalize_booking_request

    sid = req.student_id
    if not sid and req.token:
        sid = store.get_session(req.token)
    if not sid:
        sid = "student_001"

    student = store.get_user(sid) or {}
    student_name = student.get("name", "웹 유저")

    normalized = await normalize_booking_request(
        student_name, "", req.description, llm_provider,
    )
    events = store.get_student_events(sid)
    keywords = [e["content"] for e in events if e.get("event_type") == "search"]
    briefing = await generate_briefing_report(
        student_name=normalized["student_name"],
        raw_input=normalized["cleaned_request"],
        search_history=keywords,
        llm=llm_provider,
    )

    slot = store.book_slot(
        slot_id=req.slot_id,
        student_id=sid,
        student_name=normalized["student_name"],
        desc=normalized["cleaned_request"],
        briefing=briefing,
        student_phone=normalized.get("student_phone", ""),
        summary=normalized["short_summary"],
    )
    if not slot:
        return {"status": "error", "message": "해당 시간대는 이미 예약되었습니다."}

    store.add_event(sid, {
        "timestamp": _now(), "event_type": "doc_access",
        "content": f"조교 보충수업 예약 ({slot.get('ta_name', '')})",
        "detail": normalized["short_summary"][:80],
    })

    return {
        "status": "ok",
        "message": f"✅ {slot.get('date', '')} {slot.get('start_time', '')}~{slot.get('end_time', '')} "
                   f"({slot.get('ta_name', '')}) 예약이 완료되었습니다!",
        "slot": slot,
    }


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
