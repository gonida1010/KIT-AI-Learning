"""
멘토 대시보드 API — 출근 브리핑, 대기열, 학생 타임라인, 초대 링크.
"""

import uuid
from fastapi import APIRouter, HTTPException

from db.store import store
from models.schemas import BriefingSummary, StudentProfile, TimelineEvent

router = APIRouter(prefix="/api/mentor", tags=["mentor"])


@router.get("/briefing", response_model=BriefingSummary)
async def morning_briefing():
    pending = store.get_pending_handoffs()
    total = sum(len(msgs) for msgs in store.chat_logs.values())
    keywords: list[str] = []
    for events in store.student_events.values():
        for ev in events:
            if ev["event_type"] == "search":
                keywords.append(ev["content"])
    return BriefingSummary(
        total_ai_conversations=total,
        pending_handoffs=len(pending),
        resolved_last_24h=len([h for h in store.handoff_queue if h["status"] == "resolved"]),
        top_keywords=list(dict.fromkeys(keywords))[:8],
        queue=pending,
    )


@router.get("/queue")
async def get_queue():
    return store.get_pending_handoffs()


@router.post("/queue/{handoff_id}/resolve")
async def resolve_queue_item(handoff_id: str):
    if store.resolve_handoff(handoff_id):
        return {"status": "ok"}
    raise HTTPException(404, "항목 없음")


@router.get("/students")
async def list_students():
    return store.get_all_students()


@router.get("/students/by-mentor/{mentor_id}")
async def list_students_by_mentor(mentor_id: str):
    return store.get_students_by_mentor(mentor_id)


@router.get("/student/{student_id}/timeline")
async def student_timeline(student_id: str):
    student = store.get_user(student_id)
    if not student:
        raise HTTPException(404, "학생 없음")
    events = store.get_student_events(student_id)
    keywords = [e["content"] for e in events if e["event_type"] == "search"]
    return StudentProfile(
        id=student_id,
        name=student["name"],
        career_pref=student.get("career_pref", ""),
        events=[TimelineEvent(**e) for e in events],
        frequent_keywords=keywords,
    )


# ── 초대 링크 ────────────────────────────────────────────
@router.post("/invite")
async def create_invite(mentor_id: str = "mentor_001"):
    mentor = store.get_user(mentor_id)
    if not mentor or mentor["role"] != "mentor":
        raise HTTPException(404, "멘토 없음")
    code = mentor.get("invite_code")
    if not code:
        code = uuid.uuid4().hex[:8].upper()
        mentor["invite_code"] = code
        store.invite_codes[code] = mentor_id
        store._save()
    else:
        store.invite_codes[code] = mentor_id
        store._save()
    return {"invite_code": code, "invite_url": f"/?invite={code}"}
