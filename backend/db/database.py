"""
SQLAlchemy 엔진 및 세션 팩토리.
DATABASE_URL 설정 시 PostgreSQL, 미설정 시 SQLite(로컬 개발용).
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Render 등에서 postgres:// 로 시작하는 URL을 postgresql:// 로 변환
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# DATABASE_URL 미설정 시 SQLite 사용 (로컬 개발용)
if not DATABASE_URL:
    _db_path = Path(__file__).resolve().parent / "app.db"
    DATABASE_URL = f"sqlite:///{_db_path}"

_is_sqlite = DATABASE_URL.startswith("sqlite")
_engine_kwargs = {"pool_pre_ping": True}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """FastAPI Depends 또는 수동 사용 가능한 세션 제너레이터."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """모든 테이블 생성 (없으면 CREATE) + 마이그레이션."""
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate():
    """기존 테이블에 새 컬럼/인덱스 추가 (없으면)."""
    insp = inspect(engine)
    _add_column_if_missing(insp, "mentor_docs", "file_data", "BYTEA")
    _add_column_if_missing(insp, "mentor_docs", "source_excerpt", "TEXT")
    _add_column_if_missing(insp, "mentor_basic_docs", "file_data", "BYTEA")
    _add_column_if_missing(insp, "mentor_basic_docs", "source_excerpt", "TEXT")
    _create_indexes_if_missing()


def _add_column_if_missing(insp, table: str, column: str, col_type: str):
    if not insp.has_table(table):
        return
    existing = {c["name"] for c in insp.get_columns(table)}
    if column not in existing:
        with engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))


def _create_indexes_if_missing():
    """기존 배포 DB 에 누락된 인덱스 추가."""
    _indexes = [
        ("ix_users_role", "users", "role"),
        ("ix_users_mentor_id", "users", "mentor_id"),
        ("ix_chat_messages_role", "chat_messages", "role"),
        ("ix_chat_messages_created_at", "chat_messages", "created_at"),
        ("ix_handoff_queue_student_id", "handoff_queue", "student_id"),
        ("ix_handoff_queue_status", "handoff_queue", "status"),
        ("ix_schedules_is_available", "schedules", "is_available"),
        ("ix_schedules_booked_by", "schedules", "booked_by"),
        ("ix_student_events_timestamp", "student_events", "timestamp"),
    ]
    insp = inspect(engine)
    with engine.begin() as conn:
        for idx_name, table, column in _indexes:
            if not insp.has_table(table):
                continue
            existing_idx = {i["name"] for i in insp.get_indexes(table)}
            if idx_name not in existing_idx:
                try:
                    conn.execute(text(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"
                    ))
                except Exception:
                    pass
