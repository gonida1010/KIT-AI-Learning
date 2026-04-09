"""Pydantic 스키마 — Edu-Sync AI 전체 데이터 모델."""

from __future__ import annotations
from pydantic import BaseModel


# ── Chat ─────────────────────────────────────────────────
class Choice(BaseModel):
    label: str
    description: str


# ── Handoff ──────────────────────────────────────────────
class HandoffRequest(BaseModel):
    id: str = ""
    student_id: str
    student_name: str = ""
    reason: str = ""
    last_message: str = ""
    priority: str = "medium"
    status: str = "pending"
    created_at: str = ""


# ── Mentor Briefing ─────────────────────────────────────
class BriefingSummary(BaseModel):
    total_ai_conversations: int = 0
    pending_handoffs: int = 0
    resolved_last_24h: int = 0
    top_keywords: list[str] = []
    queue: list[HandoffRequest] = []


# ── Student Timeline ────────────────────────────────────
class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str
    content: str
    detail: str = ""


class StudentProfile(BaseModel):
    id: str
    name: str
    career_pref: str = ""
    events: list[TimelineEvent] = []
    frequent_keywords: list[str] = []


# ── TA Scheduling ───────────────────────────────────────
class TASlot(BaseModel):
    id: str = ""
    ta_id: str = ""
    ta_name: str
    date: str
    start_time: str
    end_time: str
    slot_type: str = "available"
    unavailable_reason: str | None = None
    is_available: bool = True
    booked_by: str | None = None
    booked_by_name: str | None = None
    booking_description: str | None = None
    briefing_report: dict | None = None


class BookingRequest(BaseModel):
    slot_id: str
    student_id: str = "student_001"
    student_name: str = "김민수"
    description: str


# ── Knowledge Base ──────────────────────────────────────
class KnowledgeDoc(BaseModel):
    id: str = ""
    filename: str
    doc_type: str = "기타"
    uploaded_at: str = ""
    chunk_count: int = 0


# ── Curation ────────────────────────────────────────────
class CurationItem(BaseModel):
    id: str = ""
    category: str
    title: str
    summary: str
    content: str
    date: str
    weekday: int = 0
    source_filename: str = ""
    tags: list[str] = []
    created_at: str = ""
