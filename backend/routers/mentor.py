"""멘토 대시보드 API — 출근 브리핑, 대기열 관리, 학생 타임라인."""

from fastapi import APIRouter, HTTPException

from db.store import store
from models.schemas import BriefingSummary, StudentProfile, TimelineEvent

router = APIRouter(prefix="/api/mentor", tags=["mentor"])


@router.get("/briefing", response_model=BriefingSummary)
async def morning_briefing():
    """출근 브리핑 — 밤사이 대화 요약 + 대기열 현황."""
    pending = store.get_pending_handoffs()

    # 최근 24시간 대화 수 집계
    total_convos = sum(len(msgs) for msgs in store.conversations.values())

    # 상위 키워드 수집
    all_keywords: list[str] = []
    for events in store.student_events.values():
        for ev in events:
            if ev["event_type"] == "search":
                all_keywords.append(ev["content"])

    return BriefingSummary(
        total_ai_conversations=total_convos,
        pending_handoffs=len(pending),
        resolved_last_24h=len([h for h in store.handoff_queue if h["status"] == "resolved"]),
        top_keywords=list(dict.fromkeys(all_keywords))[:8],  # 중복 제거, 최대 8개
        queue=pending,
    )


@router.get("/queue")
async def get_queue():
    """대기열 목록."""
    return store.get_pending_handoffs()


@router.post("/queue/{handoff_id}/resolve")
async def resolve_queue_item(handoff_id: str):
    """대기열 항목 해결."""
    if store.resolve_handoff(handoff_id):
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="해당 항목을 찾을 수 없습니다.")


@router.get("/students")
async def list_students():
    """전체 학생 목록."""
    return store.get_all_students()


@router.get("/student/{student_id}/timeline")
async def student_timeline(student_id: str):
    """학생별 히스토리 아카이브 타임라인."""
    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    events = store.get_student_events(student_id)
    keywords = [e["content"] for e in events if e["event_type"] == "search"]

    return StudentProfile(
        id=student_id,
        name=student["name"],
        events=[TimelineEvent(**e) for e in events],
        frequent_keywords=keywords,
    )
