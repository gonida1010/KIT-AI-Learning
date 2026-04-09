"""조교(TA) 스케줄링 API — 빈 시간 예약 + AI 브리핑 리포트 + 반복 슬롯 생성."""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.store import store
from models.schemas import BookingRequest, TASlot

router = APIRouter(prefix="/api/ta", tags=["ta"])


def _uid():
    return uuid.uuid4().hex[:12]


class RecurringSlotRequest(BaseModel):
    ta_id: str
    ta_name: str
    weekdays: list[int]       # 0=월 ~ 4=금
    start_time: str           # "14:00"
    end_time: str             # "15:00"
    weeks: int = 4            # 몇 주간 생성
    slot_type: str = "available"
    unavailable_reason: str | None = None


class BulkSlotRequest(BaseModel):
    ta_id: str
    ta_name: str
    start_date: str
    end_date: str
    weekdays: list[int]
    start_time: str
    end_time: str
    slot_type: str = "available"
    unavailable_reason: str | None = None


class BaseScheduleRequest(BaseModel):
    ta_id: str
    ta_name: str
    start_date: str
    end_date: str
    weekdays: list[int]


@router.get("/slots")
async def get_slots():
    return store.get_all_slots()


@router.get("/available")
async def get_available():
    return store.get_available_slots()


@router.post("/book")
async def book_slot(req: BookingRequest):
    from main import llm_provider
    from services.agent_b import generate_briefing_report

    events = store.get_student_events(req.student_id)
    keywords = [e["content"] for e in events if e["event_type"] == "search"]

    briefing = await generate_briefing_report(
        student_name=req.student_name,
        raw_input=req.description,
        search_history=keywords,
        llm=llm_provider,
    )

    slot = store.book_slot(
        slot_id=req.slot_id,
        student_id=req.student_id,
        student_name=req.student_name,
        desc=req.description,
        briefing=briefing,
    )
    if not slot:
        raise HTTPException(400, "해당 시간대는 이미 예약됨")

    store.add_event(req.student_id, {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": "doc_access",
        "content": f"조교 보충수업 예약 ({slot['ta_name']})",
        "detail": req.description[:80],
    })

    return {"status": "ok", "slot": slot, "briefing": briefing}


@router.get("/briefings")
async def get_briefings():
    return [s for s in store.get_booked_slots() if s.get("briefing_report")]


@router.post("/slots")
async def add_slot(slot: TASlot):
    d = slot.model_dump()
    d["id"] = _uid()
    store.add_ta_slot(d)
    return {"status": "ok", "slot": d}


@router.post("/slots/recurring")
async def add_recurring_slots(req: RecurringSlotRequest):
    """반복 슬롯 일괄 생성 — 지정 요일/시간을 N주간 자동 생성."""
    created = []
    today = datetime.now().date()
    # 이번 주 월요일 기준
    monday = today - timedelta(days=today.weekday())

    for week in range(req.weeks):
        for wd in req.weekdays:
            target = monday + timedelta(weeks=week, days=wd)
            if target < today:
                continue
            date_str = target.strftime("%Y-%m-%d")
            # 중복 체크
            exists = any(
                s["ta_id"] == req.ta_id
                and s["date"] == date_str
                and s["start_time"] == req.start_time
                for s in store.schedules
            )
            if exists:
                continue
            slot = {
                "id": _uid(),
                "ta_id": req.ta_id,
                "ta_name": req.ta_name,
                "date": date_str,
                "start_time": req.start_time,
                "end_time": req.end_time,
                "slot_type": req.slot_type,
                "unavailable_reason": req.unavailable_reason,
                "is_available": req.slot_type == "available",
                "booked_by": None,
                "booked_by_name": None,
                "booking_description": None,
                "briefing_report": None,
            }
            store.add_ta_slot(slot)
            created.append(slot)

    return {"status": "ok", "created_count": len(created), "slots": created}


@router.post("/slots/bulk")
async def add_bulk_slots(req: BulkSlotRequest):
    start = datetime.strptime(req.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(req.end_date, "%Y-%m-%d").date()
    if end < start:
        raise HTTPException(400, "종료 날짜는 시작 날짜보다 빠를 수 없습니다.")

    created = []
    current = start
    while current <= end:
        weekday = current.weekday()
        if weekday in req.weekdays:
            date_str = current.strftime("%Y-%m-%d")
            exists = any(
                s["ta_id"] == req.ta_id
                and s["date"] == date_str
                and s["start_time"] == req.start_time
                and s["end_time"] == req.end_time
                for s in store.schedules
            )
            if not exists:
                slot = {
                    "id": _uid(),
                    "ta_id": req.ta_id,
                    "ta_name": req.ta_name,
                    "date": date_str,
                    "start_time": req.start_time,
                    "end_time": req.end_time,
                    "slot_type": req.slot_type,
                    "unavailable_reason": req.unavailable_reason,
                    "is_available": req.slot_type == "available",
                    "booked_by": None,
                    "booked_by_name": None,
                    "booking_description": None,
                    "briefing_report": None,
                }
                store.add_ta_slot(slot)
                created.append(slot)
        current += timedelta(days=1)

    return {"status": "ok", "created_count": len(created), "slots": created}


@router.post("/slots/base-template")
async def add_base_template_slots(req: BaseScheduleRequest):
    start = datetime.strptime(req.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(req.end_date, "%Y-%m-%d").date()
    if end < start:
        raise HTTPException(400, "종료 날짜는 시작 날짜보다 빠를 수 없습니다.")

    created = []
    current = start
    while current <= end:
        weekday = current.weekday()
        if weekday in req.weekdays:
            date_str = current.strftime("%Y-%m-%d")
            for hour in range(9, 22):
                start_time = f"{hour:02d}:00"
                end_time = f"{hour + 1:02d}:00"
                exists = any(
                    s["ta_id"] == req.ta_id
                    and s["date"] == date_str
                    and s["start_time"] == start_time
                    and s["end_time"] == end_time
                    for s in store.schedules
                )
                if exists:
                    continue
                slot = {
                    "id": _uid(),
                    "ta_id": req.ta_id,
                    "ta_name": req.ta_name,
                    "date": date_str,
                    "start_time": start_time,
                    "end_time": end_time,
                    "slot_type": "available",
                    "unavailable_reason": None,
                    "is_available": True,
                    "booked_by": None,
                    "booked_by_name": None,
                    "booking_description": None,
                    "briefing_report": None,
                }
                store.add_ta_slot(slot)
                created.append(slot)
        current += timedelta(days=1)

    return {"status": "ok", "created_count": len(created), "slots": created}


@router.delete("/slots/{slot_id}")
async def delete_slot(slot_id: str):
    """슬롯 삭제 (예약되지 않은 슬롯만)."""
    for i, s in enumerate(store.schedules):
        if s["id"] == slot_id:
            if s.get("booked_by"):
                raise HTTPException(400, "이미 예약된 슬롯은 삭제할 수 없습니다.")
            store.schedules.pop(i)
            store._save()
            return {"status": "ok"}
    raise HTTPException(404, "슬롯을 찾을 수 없습니다.")
