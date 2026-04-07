"""Pydantic 스키마 — Edu-Sync AI 전체 데이터 모델."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ─── Chat (내부 저장용 — 카카오 웹훅에서 사용) ──────────────
class Choice(BaseModel):
    label: str
    description: str


# ─── Handoff Queue ──────────────────────────────────────────
class HandoffRequest(BaseModel):
    id: str = ""
    student_id: str
    student_name: str = ""
    reason: str = ""
    last_message: str = ""
    priority: str = "medium"  # high | medium | low
    status: str = "pending"   # pending | in_progress | resolved
    created_at: str = ""


# ─── Mentor Briefing ────────────────────────────────────────
class BriefingSummary(BaseModel):
    total_ai_conversations: int = 0
    pending_handoffs: int = 0
    resolved_last_24h: int = 0
    top_keywords: list[str] = []
    queue: list[HandoffRequest] = []


# ─── Student Timeline ───────────────────────────────────────
class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # "search" | "doc_access" | "chat" | "handoff"
    content: str
    detail: str = ""


class StudentProfile(BaseModel):
    id: str
    name: str
    events: list[TimelineEvent] = []
    chat_summary: str = ""
    frequent_keywords: list[str] = []


# ─── TA Scheduling ──────────────────────────────────────────
class TASlot(BaseModel):
    id: str = ""
    ta_name: str
    date: str       # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str
    is_available: bool = True
    booked_by: str | None = None
    booked_by_name: str | None = None
    booking_description: str | None = None
    briefing_report: dict | None = None


class BookingRequest(BaseModel):
    slot_id: str
    student_id: str = "student_1"
    student_name: str = "김민수"
    description: str  # 수강생의 자유 입력


# ─── Knowledge Base ─────────────────────────────────────────
class KnowledgeDoc(BaseModel):
    id: str = ""
    filename: str
    doc_type: str = "기타"  # 규정, 공모전, 자소서, 취업, 커리큘럼
    uploaded_at: str = ""
    chunk_count: int = 0


# ─── CurriMap (기존 분석) ────────────────────────────────────
class AnalysisResult(BaseModel):
    location: str
    progress_percentage: int
    why_learn: str
    whats_next: str
    glossary: dict[str, str]
