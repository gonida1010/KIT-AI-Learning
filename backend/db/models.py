"""
SQLAlchemy ORM 모델 — 기존 JSON 스토어 구조를 테이블로 매핑.
"""

from sqlalchemy import Boolean, Column, Integer, LargeBinary, String, Text, JSON

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    kakao_id = Column(String, unique=True, nullable=True, index=True)
    name = Column(String, nullable=False)
    profile_image = Column(String, default="")
    role = Column(String, nullable=False)  # student, mentor, ta, admin
    mentor_id = Column(String, nullable=True)
    invite_code = Column(String, nullable=True)
    career_pref = Column(String, nullable=True)
    created_at = Column(String, nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    type = Column(String, default="kakao")
    created_at = Column(String, nullable=False)


class QRSession(Base):
    __tablename__ = "qr_sessions"

    token = Column(String, primary_key=True)
    status = Column(String, default="pending")
    user_id = Column(String, nullable=True)
    session_token = Column(String, nullable=True)
    created_at = Column(String, nullable=False)


class InviteCode(Base):
    __tablename__ = "invite_codes"

    code = Column(String, primary_key=True)
    mentor_id = Column(String, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=True)
    role = Column(String, nullable=False)  # user, assistant
    agent_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    choices = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(String, nullable=False)


class Handoff(Base):
    __tablename__ = "handoff_queue"

    id = Column(String, primary_key=True)
    student_id = Column(String, nullable=False)
    student_name = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    last_message = Column(Text, nullable=True)
    priority = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(String, nullable=True)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True)
    ta_id = Column(String, nullable=True)
    ta_name = Column(String, nullable=True)
    date = Column(String, nullable=True, index=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    booked_by = Column(String, nullable=True)
    booked_by_name = Column(String, nullable=True)
    booking_phone = Column(String, nullable=True)
    booking_description = Column(Text, nullable=True)
    booking_summary = Column(Text, nullable=True)
    briefing_report = Column(JSON, nullable=True)
    slot_type = Column(String, default="available")
    unavailable_reason = Column(String, nullable=True)


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=True)
    doc_type = Column(String, nullable=True)
    uploaded_at = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)


class MentorDoc(Base):
    __tablename__ = "mentor_docs"

    id = Column(String, primary_key=True)
    mentor_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=True)
    source_filename = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_kind = Column(String, nullable=True)  # file, link, image
    digest_title = Column(String, nullable=True)
    digest_summary = Column(Text, nullable=True)
    uploaded_at = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    file_data = Column(LargeBinary, nullable=True)


class MentorBasicDoc(Base):
    """기초 자료 — 멘토가 올리는 기본 학습 자료 (최신 자료와 분리)."""
    __tablename__ = "mentor_basic_docs"

    id = Column(String, primary_key=True)
    mentor_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=True)
    source_filename = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_kind = Column(String, nullable=True)  # file, link, image
    digest_title = Column(String, nullable=True)
    digest_summary = Column(Text, nullable=True)
    uploaded_at = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    file_data = Column(LargeBinary, nullable=True)


class CurationItem(Base):
    __tablename__ = "curation_items"

    id = Column(String, primary_key=True)
    category = Column(String, nullable=True, index=True)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    date = Column(String, nullable=True, index=True)
    weekday = Column(Integer, nullable=True)
    source_filename = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    attachment_kind = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(String, nullable=True)


class StudentEvent(Base):
    __tablename__ = "student_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    content = Column(String, nullable=True)
    detail = Column(String, nullable=True)
