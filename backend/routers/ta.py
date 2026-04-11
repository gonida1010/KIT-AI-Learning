"""조교(TA) 스케줄링 API — 빈 시간 예약 + AI 브리핑 리포트 + 반복 슬롯 생성."""

import re
import uuid
from datetime import date, datetime, timedelta

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
    weekdays: list[int]
    start_time: str
    end_time: str
    weeks: int = 4
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


class ScheduleAssistantRequest(BaseModel):
    ta_id: str
    ta_name: str
    target_month: str
    message: str
    apply: bool = False
    manual_plan: dict | None = None


def _normalize_time(value: str, *, default: str) -> str:
    match = re.search(r"(\d{1,2})(?::(\d{2}))?", value or "")
    if not match:
        return default
    hour = max(0, min(23, int(match.group(1))))
    minute = match.group(2) or "00"
    return f"{hour:02d}:{minute}"


def _time_range_hours(start_time: str, end_time: str) -> set[int]:
    start_hour = int(start_time[:2])
    end_hour = int(end_time[:2])
    return {hour for hour in range(start_hour, end_hour) if 0 <= hour <= 23}


def _month_bounds(target_month: str) -> tuple[date, date]:
    start = datetime.strptime(f"{target_month}-01", "%Y-%m-%d").date()
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    return start, next_month - timedelta(days=1)


def _sanitize_rule(rule: dict) -> dict:
    weekdays = [
        int(day)
        for day in (rule.get("weekdays") or [])
        if isinstance(day, int) and 0 <= day <= 6
    ]
    return {
        "weekdays": sorted(set(weekdays)),
        "dates": [value for value in (rule.get("dates") or []) if isinstance(value, str)],
        "start_time": _normalize_time(rule.get("start_time", "09:00"), default="09:00"),
        "end_time": _normalize_time(rule.get("end_time", "22:00"), default="22:00"),
    }


def _sanitize_plan(plan: dict | None) -> dict:
    payload = plan or {}
    return {
        "mode": payload.get("mode", "full"),
        "summary": (payload.get("summary") or "").strip(),
        "available_rules": [
            _sanitize_rule(rule) for rule in (payload.get("available_rules") or [])
        ],
        "full_day_off_rules": [
            _sanitize_rule(rule)
            for rule in (payload.get("full_day_off_rules") or [])
        ],
        "partial_unavailable_rules": [
            _sanitize_rule(rule)
            for rule in (payload.get("partial_unavailable_rules") or [])
        ],
    }


def _weekday_labels(weekdays: list[int]) -> str:
    labels = ["월", "화", "수", "목", "금", "토", "일"]
    return ", ".join(labels[index] for index in weekdays if 0 <= index < len(labels))


def _summarize_plan(plan: dict) -> str:
    summary_parts = []
    if plan.get("full_day_off_rules"):
        off_labels = []
        for rule in plan["full_day_off_rules"]:
            parts = []
            label = _weekday_labels(rule.get("weekdays", []))
            if label:
                parts.append(label)
            dates = rule.get("dates", [])
            if dates:
                parts.append(", ".join(dates))
            if parts:
                off_labels.append(f"{' / '.join(parts)} 휴무")
        if off_labels:
            summary_parts.append(" / ".join(off_labels))

    if plan.get("available_rules"):
        available_labels = []
        for rule in plan["available_rules"]:
            parts = []
            label = _weekday_labels(rule.get("weekdays", []))
            if label:
                parts.append(label)
            dates = rule.get("dates", [])
            if dates:
                parts.append(", ".join(dates))
            if parts:
                available_labels.append(
                    f"{' / '.join(parts)} {rule.get('start_time', '09:00')}~{rule.get('end_time', '22:00')} 가능"
                )
        if available_labels:
            summary_parts.append(" / ".join(available_labels))

    if plan.get("partial_unavailable_rules"):
        partial_labels = []
        for rule in plan["partial_unavailable_rules"]:
            parts = []
            label = _weekday_labels(rule.get("weekdays", []))
            if label:
                parts.append(label)
            dates = rule.get("dates", [])
            if dates:
                parts.append(", ".join(dates))
            if parts:
                partial_labels.append(
                    f"{' / '.join(parts)} {rule.get('start_time', '09:00')}~{rule.get('end_time', '22:00')} 불가"
                )
        if partial_labels:
            summary_parts.append(" / ".join(partial_labels))

    return " | ".join(summary_parts) or "설정 내용을 다시 확인해 주세요."


def _fallback_schedule_plan(message: str, target_month: str = "") -> dict:
    text = (message or "").strip()
    off_weekdays: set[int] = set()
    available_weekdays: set[int] = set()

    # Check for specific date mentions (e.g., "17일", "3일, 5일")
    date_matches = re.findall(r"(\d{1,2})일", text)
    off_dates: list[str] = []
    available_dates: list[str] = []

    if date_matches and target_month:
        for day_str in date_matches:
            date_val = f"{target_month}-{int(day_str):02d}"
            if "휴무" in text or "쉬" in text or "off" in text.lower():
                off_dates.append(date_val)
            elif "가능" in text or "예약" in text:
                available_dates.append(date_val)
            else:
                off_dates.append(date_val)

    if off_dates or available_dates:
        time_match = re.search(r"(\d{1,2})\s*시\s*부터\s*(\d{1,2})\s*시\s*까지", text)
        start_time = "09:00"
        end_time = "16:00"
        if time_match:
            start_time = f"{int(time_match.group(1)):02d}:00"
            end_time = f"{int(time_match.group(2)):02d}:00"

        summary_parts = []
        if off_dates:
            summary_parts.append(f"{', '.join(off_dates)} 휴무")
        if available_dates:
            summary_parts.append(f"{', '.join(available_dates)} {start_time}~{end_time} 가능")

        return {
            "mode": "date_override",
            "summary": " / ".join(summary_parts),
            "available_rules": [
                {
                    "weekdays": [],
                    "dates": available_dates,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ] if available_dates else [],
            "full_day_off_rules": [
                {
                    "weekdays": [],
                    "dates": off_dates,
                    "start_time": "09:00",
                    "end_time": "22:00",
                }
            ] if off_dates else [],
            "partial_unavailable_rules": [],
        }

    if "주말" in text or "토일" in text:
        off_weekdays.update({5, 6})
    if "평일" in text or "월금" in text or "월~금" in text or "월-금" in text:
        available_weekdays.update({0, 1, 2, 3, 4})
    if "나머지 요일" in text and off_weekdays:
        available_weekdays.update(set(range(7)) - off_weekdays)

    time_match = re.search(r"(\d{1,2})\s*시\s*부터\s*(\d{1,2})\s*시\s*까지", text)
    start_time = "09:00"
    end_time = "16:00"
    if time_match:
        start_time = f"{int(time_match.group(1)):02d}:00"
        end_time = f"{int(time_match.group(2)):02d}:00"

    if not available_weekdays and not off_weekdays:
        available_weekdays.update({0, 1, 2, 3, 4})

    summary_parts = []
    if off_weekdays:
        summary_parts.append("토·일 전체 휴무")
    if available_weekdays:
        summary_parts.append(f"나머지 요일 {start_time}~{end_time} 예약 가능")

    return {
        "mode": "full",
        "summary": " / ".join(summary_parts) or "설정 내용을 다시 입력해 주세요.",
        "available_rules": [
            {
                "weekdays": sorted(available_weekdays),
                "dates": [],
                "start_time": start_time,
                "end_time": end_time,
            }
        ]
        if available_weekdays
        else [],
        "full_day_off_rules": [
            {
                "weekdays": sorted(off_weekdays),
                "dates": [],
                "start_time": "09:00",
                "end_time": "22:00",
            }
        ]
        if off_weekdays
        else [],
        "partial_unavailable_rules": [],
    }


async def _parse_schedule_plan(target_month: str, message: str) -> dict:
    from main import llm_provider

    prompt = f"""
당신은 조교 월간 스케줄 설정 비서입니다.
선택한 월({target_month})에 대해서만 이해하고, 조교의 자연어 지시를 월간 시간표 규칙으로 변환하세요.

mode 필드 결정:
- 사용자가 특정 날짜(예: 17일, 3일, 7월 20일 등)를 언급하면 mode: "date_override" 를 사용하세요.
  이 모드에서는 해당 날짜만 변경하고 나머지 기존 스케줄은 유지됩니다.
- 사용자가 월 전체 패턴(요일별 규칙)을 설정하면 mode: "full" 을 사용하세요.

반드시 아래 JSON 형식으로만 답변하세요:
{{
  "mode": "full 또는 date_override",
  "summary": "조교에게 보여줄 짧은 확인 문장",
  "available_rules": [
    {{"weekdays": [0, 1, 2, 3, 4], "dates": [], "start_time": "09:00", "end_time": "16:00"}}
  ],
  "full_day_off_rules": [
    {{"weekdays": [5, 6], "dates": [], "start_time": "09:00", "end_time": "22:00"}}
  ],
  "partial_unavailable_rules": [
    {{"weekdays": [2], "dates": [], "start_time": "12:00", "end_time": "13:00"}}
  ]
}}

규칙:
- 요일 인덱스는 0=월, 1=화, ..., 6=일 입니다.
- "휴무"는 full_day_off_rules 에 넣으세요.
- "예약 가능"은 available_rules 에 넣으세요.
- "점심시간", "휴식", "불가 시간"은 partial_unavailable_rules 에 넣으세요.
- 시간은 HH:MM 형식으로만 출력하세요.
- 사용자가 말하지 않은 규칙은 만들지 마세요.
- summary 는 1문장으로 짧게 작성하세요.

특정 날짜 규칙 (date_override 모드):
- 사용자가 "17일 휴무"라고 하면 dates 배열에 "{target_month}-17" 형식으로 넣으세요.
- "3일, 5일 휴무"라면 dates: ["{target_month}-03", "{target_month}-05"] 로 넣으세요.
- "20일 10시~14시 가능"이라면 available_rules의 dates에 "{target_month}-20"을 넣으세요.
- date_override 모드에서는 weekdays는 빈 배열 []로 두세요.

예시 1 — 월 전체 패턴:
입력: "토일 휴무, 평일은 09시~16시"
{{
  "mode": "full",
  "summary": "토·일 휴무, 평일 09:00~16:00 예약 가능",
  "available_rules": [{{"weekdays": [0,1,2,3,4], "dates": [], "start_time": "09:00", "end_time": "16:00"}}],
  "full_day_off_rules": [{{"weekdays": [5,6], "dates": [], "start_time": "09:00", "end_time": "22:00"}}],
  "partial_unavailable_rules": []
}}

예시 2 — 특정 날짜 변경:
입력: "17일 휴무"
{{
  "mode": "date_override",
  "summary": "{target_month}-17 휴무 추가",
  "available_rules": [],
  "full_day_off_rules": [{{"weekdays": [], "dates": ["{target_month}-17"], "start_time": "09:00", "end_time": "22:00"}}],
  "partial_unavailable_rules": []
}}

예시 3 — 특정 날짜 가능 시간 변경:
입력: "3일은 10시부터 14시까지만 가능"
{{
  "mode": "date_override",
  "summary": "{target_month}-03 10:00~14:00 예약 가능",
  "available_rules": [{{"weekdays": [], "dates": ["{target_month}-03"], "start_time": "10:00", "end_time": "14:00"}}],
  "full_day_off_rules": [],
  "partial_unavailable_rules": []
}}
"""

    if llm_provider:
        try:
            raw_plan = await llm_provider.chat_json(prompt, message)
            return _sanitize_plan(raw_plan)
        except Exception:
            pass

    return _fallback_schedule_plan(message, target_month)


def _matches_rule(target_date: date, rule: dict) -> bool:
    return (
        target_date.weekday() in rule.get("weekdays", [])
        or target_date.strftime("%Y-%m-%d") in rule.get("dates", [])
    )


def _new_slot(ta_id: str, ta_name: str, date_str: str, hour: int, slot_type: str) -> dict:
    return {
        "id": _uid(),
        "ta_id": ta_id,
        "ta_name": ta_name,
        "date": date_str,
        "start_time": f"{hour:02d}:00",
        "end_time": f"{hour + 1:02d}:00",
        "slot_type": slot_type,
        "unavailable_reason": None,
        "is_available": slot_type == "available",
        "booked_by": None,
        "booked_by_name": None,
        "booking_phone": None,
        "booking_description": None,
        "booking_summary": None,
        "briefing_report": None,
    }


def _collect_override_dates(plan: dict) -> set[str]:
    """Collect all specific dates mentioned in any rule's dates array."""
    dates: set[str] = set()
    for key in ("available_rules", "full_day_off_rules", "partial_unavailable_rules"):
        for rule in plan.get(key, []):
            dates.update(rule.get("dates", []))
    return dates


def _apply_schedule_plan(ta_id: str, ta_name: str, target_month: str, plan: dict) -> dict:
    start, end = _month_bounds(target_month)
    mode = plan.get("mode", "full")

    override_dates = _collect_override_dates(plan) if mode == "date_override" else set()

    if mode == "date_override" and override_dates:
        removed_count = 0
        for d in override_dates:
            removed_count += store.clear_unbooked_ta_slots(ta_id, d, d)
    else:
        removed_count = store.clear_unbooked_ta_slots(
            ta_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
        )

    created_slots: list[dict] = []
    preserved_booked_count = 0
    cursor = start

    while cursor <= end:
        date_str = cursor.strftime("%Y-%m-%d")

        if mode == "date_override" and date_str not in override_dates:
            cursor += timedelta(days=1)
            continue

        existing_booked_hours = {
            int(slot["start_time"][:2])
            for slot in store.schedules
            if slot.get("ta_id") == ta_id and slot.get("date") == date_str and slot.get("booked_by")
        }
        preserved_booked_count += len(existing_booked_hours)

        full_day_off = any(
            _matches_rule(cursor, rule) for rule in plan.get("full_day_off_rules", [])
        )
        if full_day_off:
            for hour in sorted(set(range(9, 22)) - existing_booked_hours):
                created_slots.append(_new_slot(ta_id, ta_name, date_str, hour, "blocked"))
            cursor += timedelta(days=1)
            continue

        available_hours: set[int] = set()
        blocked_hours: set[int] = set()

        for rule in plan.get("available_rules", []):
            if _matches_rule(cursor, rule):
                available_hours.update(_time_range_hours(rule["start_time"], rule["end_time"]))

        for rule in plan.get("partial_unavailable_rules", []):
            if _matches_rule(cursor, rule):
                blocked_hours.update(_time_range_hours(rule["start_time"], rule["end_time"]))

        blocked_hours -= existing_booked_hours
        available_hours = (available_hours - blocked_hours) - existing_booked_hours

        for hour in sorted(available_hours):
            created_slots.append(_new_slot(ta_id, ta_name, date_str, hour, "available"))
        for hour in sorted(blocked_hours):
            created_slots.append(_new_slot(ta_id, ta_name, date_str, hour, "blocked"))

        cursor += timedelta(days=1)

    store.add_ta_slots(created_slots)
    return {
        "removed_count": removed_count,
        "created_count": len(created_slots),
        "created_available_count": len(
            [slot for slot in created_slots if slot.get("slot_type") == "available"]
        ),
        "created_blocked_count": len(
            [slot for slot in created_slots if slot.get("slot_type") == "blocked"]
        ),
        "preserved_booked_count": preserved_booked_count,
    }


@router.get("/slots")
async def get_slots():
    return store.get_all_slots()


@router.get("/available")
async def get_available():
    return store.get_available_slots()


@router.post("/book")
async def book_slot(req: BookingRequest):
    from main import llm_provider
    from services.agent_b import generate_briefing_report, normalize_booking_request

    events = store.get_student_events(req.student_id)
    keywords = [e["content"] for e in events if e["event_type"] == "search"]
    student = store.get_user(req.student_id) or {}
    normalized = await normalize_booking_request(
        req.student_name or student.get("name", "수강생"),
        req.student_phone,
        req.description,
        llm_provider,
    )

    briefing = await generate_briefing_report(
        student_name=normalized["student_name"],
        raw_input=normalized["cleaned_request"],
        search_history=keywords,
        llm=llm_provider,
    )

    slot = store.book_slot(
        slot_id=req.slot_id,
        student_id=req.student_id,
        student_name=normalized["student_name"],
        desc=normalized["cleaned_request"],
        briefing=briefing,
        student_phone=normalized["student_phone"],
        summary=normalized["short_summary"],
    )
    if not slot:
        raise HTTPException(400, "해당 시간대는 이미 예약됨")

    store.add_event(
        req.student_id,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": "doc_access",
            "content": f"조교 보충수업 예약 ({slot['ta_name']})",
            "detail": normalized["short_summary"][:80],
        },
    )

    return {
        "status": "ok",
        "slot": slot,
        "briefing": briefing,
        "normalized_request": normalized,
    }


@router.get("/briefings")
async def get_briefings():
    return [slot for slot in store.get_booked_slots() if slot.get("briefing_report")]


@router.post("/schedule-assistant")
async def ta_schedule_assistant(req: ScheduleAssistantRequest):
    if not req.message.strip() and not req.manual_plan:
        raise HTTPException(400, "설정 내용을 입력해 주세요.")

    try:
        start, end = _month_bounds(req.target_month)
    except ValueError as exc:
        raise HTTPException(400, "월 형식은 YYYY-MM 이어야 합니다.") from exc

    plan = (
        _sanitize_plan(req.manual_plan)
        if req.manual_plan
        else await _parse_schedule_plan(req.target_month, req.message)
    )
    summary = (plan.get("summary") or "").strip() or _summarize_plan(plan)

    response = {
        "status": "preview",
        "target_month": req.target_month,
        "summary": summary,
        "plan": plan,
        "month_range": {
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
        },
    }
    if req.apply:
        response.update(
            {
                "status": "applied",
                "applied": _apply_schedule_plan(req.ta_id, req.ta_name, req.target_month, plan),
            }
        )
    return response


@router.post("/slots")
async def add_slot(slot: TASlot):
    data = slot.model_dump()
    data["id"] = _uid()
    store.add_ta_slot(data)
    return {"status": "ok", "slot": data}


@router.post("/slots/recurring")
async def add_recurring_slots(req: RecurringSlotRequest):
    created = []
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    for week in range(req.weeks):
        for weekday in req.weekdays:
            target = monday + timedelta(weeks=week, days=weekday)
            if target < today:
                continue
            date_str = target.strftime("%Y-%m-%d")
            exists = any(
                slot["ta_id"] == req.ta_id
                and slot["date"] == date_str
                and slot["start_time"] == req.start_time
                for slot in store.schedules
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
                "booking_phone": None,
                "booking_description": None,
                "booking_summary": None,
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
        if current.weekday() in req.weekdays:
            date_str = current.strftime("%Y-%m-%d")
            exists = any(
                slot["ta_id"] == req.ta_id
                and slot["date"] == date_str
                and slot["start_time"] == req.start_time
                and slot["end_time"] == req.end_time
                for slot in store.schedules
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
                    "booking_phone": None,
                    "booking_description": None,
                    "booking_summary": None,
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
        if current.weekday() in req.weekdays:
            date_str = current.strftime("%Y-%m-%d")
            for hour in range(9, 22):
                start_time = f"{hour:02d}:00"
                end_time = f"{hour + 1:02d}:00"
                exists = any(
                    slot["ta_id"] == req.ta_id
                    and slot["date"] == date_str
                    and slot["start_time"] == start_time
                    and slot["end_time"] == end_time
                    for slot in store.schedules
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
                    "booking_phone": None,
                    "booking_description": None,
                    "booking_summary": None,
                    "briefing_report": None,
                }
                store.add_ta_slot(slot)
                created.append(slot)
        current += timedelta(days=1)

    return {"status": "ok", "created_count": len(created), "slots": created}


@router.delete("/slots/{slot_id}")
async def delete_slot(slot_id: str):
    # 먼저 슬롯 조회
    slot = next((s for s in store.get_all_slots() if s["id"] == slot_id), None)
    if not slot:
        raise HTTPException(404, "슬롯을 찾을 수 없습니다.")
    if slot.get("booked_by"):
        raise HTTPException(400, "이미 예약된 슬롯은 삭제할 수 없습니다.")
    store.remove_slot(slot_id)
    return {"status": "ok"}
