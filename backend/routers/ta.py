"""조교(TA) 스케줄링 API — 빈 시간 예약 + AI 브리핑 리포트."""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException

from db.store import store
from models.schemas import BookingRequest, TASlot
from services.briefing import generate_briefing_report

router = APIRouter(prefix="/api/ta", tags=["ta"])


def _uid():
    return uuid.uuid4().hex[:12]


@router.get("/slots")
async def get_slots():
    """전체 슬롯 (예약 가능 + 예약됨)."""
    return store.get_all_slots()


@router.get("/available")
async def get_available():
    """예약 가능한 슬롯만."""
    return store.get_available_slots()


@router.post("/book")
async def book_slot(req: BookingRequest):
    """슬롯 예약 + AI 브리핑 리포트 자동 생성."""
    from main import llm  # lazy import

    # 학생 검색 이력 가져오기
    events = store.get_student_events(req.student_id)
    search_keywords = [e["content"] for e in events if e["event_type"] == "search"]

    # AI 브리핑 리포트 생성
    briefing = await generate_briefing_report(
        student_name=req.student_name,
        raw_input=req.description,
        search_history=search_keywords,
        llm=llm,
    )

    slot = store.book_slot(
        slot_id=req.slot_id,
        student_id=req.student_id,
        student_name=req.student_name,
        description=req.description,
        briefing=briefing,
    )

    if not slot:
        raise HTTPException(status_code=400, detail="해당 시간대는 이미 예약되었습니다.")

    # 이벤트 기록
    store.add_event(req.student_id, {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": "doc_access",
        "content": f"조교 보충수업 예약 ({slot['ta_name']})",
        "detail": req.description[:80],
    })

    return {"status": "ok", "slot": slot, "briefing": briefing}


@router.get("/briefings")
async def get_briefings():
    """예약된 슬롯의 브리핑 리포트 목록."""
    booked = store.get_booked_slots()
    return [s for s in booked if s.get("briefing_report")]


@router.post("/slots")
async def add_slot(slot: TASlot):
    """조교가 빈 시간대를 추가."""
    slot_dict = slot.model_dump()
    slot_dict["id"] = _uid()
    store.add_ta_slot(slot_dict)
    return {"status": "ok", "slot": slot_dict}
