"""
PostgreSQL 기반 데이터 저장소.
기존 JSON Store 와 동일한 공개 API 를 유지하며 SQLAlchemy ORM 으로 구현.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

from db.database import SessionLocal, init_db
from db.models import (
    ChatMessage,
    CurationItem,
    Handoff,
    InviteCode,
    KnowledgeDoc,
    MentorBasicDoc,
    MentorDoc,
    QRSession,
    Schedule,
    Session,
    StudentEvent,
    User,
)

_KST = timezone(timedelta(hours=9))


def _now() -> str:
    return datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S")


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def _row_to_dict(row) -> dict:
    """SQLAlchemy 모델 인스턴스를 dict 로 변환 (바이너리 컬럼 제외)."""
    d = {}
    for c in row.__table__.columns:
        if str(c.type) == "LARGE_BINARY" or c.key == "file_data":
            continue
        d[c.key] = getattr(row, c.key)
    # metadata_ 컬럼은 metadata 키로 반환
    if "metadata_" in d:
        d["metadata"] = d.pop("metadata_")
    return d


class Store:
    """PostgreSQL 기반 Store — 기존 JSON Store 와 API 호환."""

    def __init__(self):
        init_db()
        if os.getenv("SEED_DATA", "0") == "1":
            self._seed_if_empty()

    # ── helper ───────────────────────────────────────────
    @staticmethod
    def _session():
        return SessionLocal()

    # ── _save() 호환 (no-op) ─────────────────────────────
    def _save(self):
        """DB 자동 커밋이므로 no-op. 기존 코드 호환용."""
        pass

    # ━━━━━━━━━━━━━━━━━━━━━━━ User CRUD ━━━━━━━━━━━━━━━━━━
    def create_user(self, data: dict) -> dict:
        with self._session() as db:
            row = User(**data)
            db.merge(row)
            db.commit()
        return data

    def get_user(self, user_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(User, user_id)
            return _row_to_dict(row) if row else None

    def get_user_by_kakao_id(self, kakao_id: str) -> dict | None:
        with self._session() as db:
            row = db.query(User).filter(User.kakao_id == kakao_id).first()
            return _row_to_dict(row) if row else None

    def get_all_users(self) -> list[dict]:
        with self._session() as db:
            return [_row_to_dict(r) for r in db.query(User).all()]

    def get_students_by_mentor(self, mentor_id: str) -> list[dict]:
        with self._session() as db:
            rows = db.query(User).filter(
                User.role == "student", User.mentor_id == mentor_id
            ).all()
            return [_row_to_dict(r) for r in rows]

    def update_user(self, user_id: str, updates: dict) -> dict | None:
        with self._session() as db:
            row = db.get(User, user_id)
            if not row:
                return None
            for k, v in updates.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            db.commit()
            db.refresh(row)
            return _row_to_dict(row)

    # ━━━━━━━━━━━━━━━━━━━━━━ Sessions ━━━━━━━━━━━━━━━━━━━━
    def create_session(self, token: str, user_id: str, stype: str = "kakao"):
        with self._session() as db:
            db.merge(Session(token=token, user_id=user_id, type=stype, created_at=_now()))
            db.commit()
        return token

    def get_session(self, token: str) -> str | None:
        with self._session() as db:
            row = db.get(Session, token)
            return row.user_id if row else None

    def delete_session(self, token: str):
        with self._session() as db:
            row = db.get(Session, token)
            if row:
                db.delete(row)
                db.commit()

    # ━━━━━━━━━━━━━━━━━━━━ QR Sessions ━━━━━━━━━━━━━━━━━━━
    def get_qr_session(self, token: str) -> dict | None:
        with self._session() as db:
            row = db.get(QRSession, token)
            return _row_to_dict(row) if row else None

    def set_qr_session(self, token: str, data: dict):
        with self._session() as db:
            db.merge(QRSession(
                token=token,
                status=data.get("status", "pending"),
                user_id=data.get("user_id"),
                session_token=data.get("session_token"),
                created_at=data.get("created_at", _now()),
            ))
            db.commit()

    def update_qr_session(self, token: str, updates: dict):
        with self._session() as db:
            row = db.get(QRSession, token)
            if row:
                for k, v in updates.items():
                    if hasattr(row, k):
                        setattr(row, k, v)
                db.commit()

    # ━━━━━━━━━━━━━━━━━━━ Invite Codes ━━━━━━━━━━━━━━━━━━━
    def get_invite_code(self, code: str) -> str | None:
        """초대 코드로 mentor_id 조회."""
        with self._session() as db:
            row = db.get(InviteCode, code)
            return row.mentor_id if row else None

    def set_invite_code(self, code: str, mentor_id: str):
        with self._session() as db:
            db.merge(InviteCode(code=code, mentor_id=mentor_id))
            db.commit()

    # ━━━━━━━━━━━━━━━━━━━━ Chat logs ━━━━━━━━━━━━━━━━━━━━━
    def add_message(self, user_id: str, msg: dict):
        with self._session() as db:
            db.add(ChatMessage(
                id=msg.get("id", _uid()),
                user_id=user_id,
                channel=msg.get("channel"),
                role=msg.get("role", "user"),
                agent_type=msg.get("agent_type"),
                content=msg.get("content"),
                choices=msg.get("choices"),
                metadata_=msg.get("metadata"),
                created_at=msg.get("created_at", _now()),
            ))
            db.commit()

    def get_conversation(self, user_id: str) -> list[dict]:
        with self._session() as db:
            rows = (
                db.query(ChatMessage)
                .filter(ChatMessage.user_id == user_id)
                .order_by(ChatMessage.created_at)
                .all()
            )
            return [_row_to_dict(r) for r in rows]

    # ━━━━━━━━━━━━━━━━━━━━ Handoff ━━━━━━━━━━━━━━━━━━━━━━━
    def add_handoff(self, item: dict):
        with self._session() as db:
            db.add(Handoff(**{k: v for k, v in item.items() if hasattr(Handoff, k)}))
            db.commit()

    def get_pending_handoffs(self) -> list[dict]:
        with self._session() as db:
            rows = db.query(Handoff).filter(Handoff.status == "pending").all()
            return [_row_to_dict(r) for r in rows]

    def resolve_handoff(self, hid: str) -> bool:
        with self._session() as db:
            row = db.get(Handoff, hid)
            if row:
                row.status = "resolved"
                db.commit()
                return True
        return False

    def resolve_handoffs_by_student(self, student_id: str) -> int:
        with self._session() as db:
            rows = (
                db.query(Handoff)
                .filter(Handoff.student_id == student_id, Handoff.status == "pending")
                .all()
            )
            for r in rows:
                r.status = "resolved"
            db.commit()
            return len(rows)

    # ━━━━━━━━━━━━━━━━━━━ TA Schedules ━━━━━━━━━━━━━━━━━━━
    def get_available_slots(self) -> list[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        max_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        with self._session() as db:
            rows = (
                db.query(Schedule)
                .filter(
                    Schedule.is_available == True,
                    Schedule.date >= today,
                    Schedule.date <= max_date,
                    Schedule.slot_type.in_(["available", None]),
                )
                .all()
            )
            return [_row_to_dict(r) for r in rows]

    def get_all_slots(self) -> list[dict]:
        with self._session() as db:
            return [_row_to_dict(r) for r in db.query(Schedule).all()]

    @property
    def schedules(self) -> list[dict]:
        """기존 store.schedules 직접 접근 호환용 property."""
        return self.get_all_slots()

    def book_slot(
        self,
        slot_id,
        student_id,
        student_name,
        desc,
        briefing=None,
        student_phone=None,
        summary=None,
    ):
        with self._session() as db:
            row = db.get(Schedule, slot_id)
            if not row or not row.is_available:
                return None
            if row.slot_type and row.slot_type != "available":
                return None
            row.is_available = False
            row.booked_by = student_id
            row.booked_by_name = student_name
            row.booking_phone = student_phone
            row.booking_description = desc
            row.booking_summary = summary
            row.briefing_report = briefing
            db.commit()
            db.refresh(row)
            return _row_to_dict(row)

    def get_booked_slots(self) -> list[dict]:
        with self._session() as db:
            rows = (
                db.query(Schedule)
                .filter(Schedule.is_available == False, Schedule.booked_by.isnot(None))
                .all()
            )
            return [_row_to_dict(r) for r in rows]

    def get_booked_slots_by_student(self, student_id: str) -> list[dict]:
        with self._session() as db:
            rows = (
                db.query(Schedule)
                .filter(Schedule.booked_by == student_id)
                .order_by(Schedule.date, Schedule.start_time)
                .all()
            )
            return [_row_to_dict(r) for r in rows]

    def cancel_booking(self, slot_id: str, student_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(Schedule, slot_id)
            if not row or row.booked_by != student_id:
                return None
            row.is_available = True
            row.booked_by = None
            row.booked_by_name = None
            row.booking_phone = None
            row.booking_description = None
            row.booking_summary = None
            row.briefing_report = None
            db.commit()
            db.refresh(row)
            return _row_to_dict(row)

    def add_ta_slot(self, slot: dict):
        with self._session() as db:
            db.merge(Schedule(**{k: v for k, v in slot.items() if hasattr(Schedule, k)}))
            db.commit()

    def add_ta_slots(self, slots: list[dict]):
        if not slots:
            return
        with self._session() as db:
            for s in slots:
                db.merge(Schedule(**{k: v for k, v in s.items() if hasattr(Schedule, k)}))
            db.commit()

    def clear_unbooked_ta_slots(self, ta_id: str, start_date: str, end_date: str) -> int:
        with self._session() as db:
            rows = (
                db.query(Schedule)
                .filter(
                    Schedule.ta_id == ta_id,
                    Schedule.date >= start_date,
                    Schedule.date <= end_date,
                    Schedule.booked_by.is_(None),
                )
                .all()
            )
            count = len(rows)
            for r in rows:
                db.delete(r)
            db.commit()
            return count

    def remove_slot(self, slot_id: str) -> bool:
        """슬롯 삭제 (ta.py 에서 store.schedules.pop 대체)."""
        with self._session() as db:
            row = db.get(Schedule, slot_id)
            if row:
                db.delete(row)
                db.commit()
                return True
        return False

    def get_ta_bookings_for_mentor(self, mentor_id: str) -> list[dict]:
        with self._session() as db:
            students = (
                db.query(User)
                .filter(User.role == "student", User.mentor_id == mentor_id)
                .all()
            )
            student_map = {s.id: s.name for s in students}
            if not student_map:
                return []
            rows = (
                db.query(Schedule)
                .filter(Schedule.booked_by.in_(list(student_map.keys())))
                .all()
            )
            items = []
            for slot in rows:
                items.append({
                    "slot_id": slot.id,
                    "ta_id": slot.ta_id or "",
                    "ta_name": slot.ta_name or "",
                    "student_id": slot.booked_by,
                    "student_name": slot.booked_by_name or student_map.get(slot.booked_by, ""),
                    "booking_phone": slot.booking_phone or "",
                    "booking_description": slot.booking_description or "",
                    "booking_summary": slot.booking_summary or "",
                    "date": slot.date or "",
                    "start_time": slot.start_time or "",
                    "end_time": slot.end_time or "",
                })
            return sorted(items, key=lambda x: f"{x['date']} {x['start_time']}", reverse=True)

    # ━━━━━━━━━━━━━━━━━━ Student events ━━━━━━━━━━━━━━━━━━
    def add_event(self, user_id: str, event: dict):
        with self._session() as db:
            db.add(StudentEvent(
                user_id=user_id,
                timestamp=event.get("timestamp", _now()),
                event_type=event.get("event_type"),
                content=event.get("content"),
                detail=event.get("detail"),
            ))
            db.commit()

    def get_student_events(self, user_id: str) -> list[dict]:
        with self._session() as db:
            rows = (
                db.query(StudentEvent)
                .filter(StudentEvent.user_id == user_id)
                .order_by(StudentEvent.timestamp)
                .all()
            )
            return [
                {
                    "timestamp": r.timestamp,
                    "event_type": r.event_type,
                    "content": r.content,
                    "detail": r.detail,
                }
                for r in rows
            ]

    def get_student(self, sid: str) -> dict | None:
        return self.get_user(sid)

    def get_all_students(self) -> list[dict]:
        with self._session() as db:
            rows = db.query(User).filter(User.role == "student").all()
            return [_row_to_dict(r) for r in rows]

    # ━━━━━━━━━━━━━━━━━━ Knowledge docs ━━━━━━━━━━━━━━━━━━
    def add_knowledge_doc(self, doc: dict):
        with self._session() as db:
            db.add(KnowledgeDoc(**{k: v for k, v in doc.items() if hasattr(KnowledgeDoc, k)}))
            db.commit()

    def get_knowledge_docs(self) -> list[dict]:
        with self._session() as db:
            return [_row_to_dict(r) for r in db.query(KnowledgeDoc).all()]

    def remove_knowledge_doc(self, doc_id: str) -> bool:
        with self._session() as db:
            row = db.get(KnowledgeDoc, doc_id)
            if row:
                db.delete(row)
                db.commit()
                return True
        return False

    # ━━━━━━━━━━━━━━━━━━ Mentor docs ━━━━━━━━━━━━━━━━━━━━━
    def add_mentor_doc(self, doc: dict):
        with self._session() as db:
            db.add(MentorDoc(**{k: v for k, v in doc.items() if hasattr(MentorDoc, k)}))
            db.commit()

    def get_mentor_docs(self, mentor_id: str, query: str | None = None, limit: int | None = None) -> list[dict]:
        with self._session() as db:
            q = db.query(MentorDoc).filter(MentorDoc.mentor_id == mentor_id)
            if query:
                like = f"%{query.lower()}%"
                q = q.filter(
                    MentorDoc.digest_title.ilike(like)
                    | MentorDoc.digest_summary.ilike(like)
                    | MentorDoc.filename.ilike(like)
                )
            q = q.order_by(MentorDoc.uploaded_at.desc())
            if limit:
                q = q.limit(limit)
            return [_row_to_dict(r) for r in q.all()]

    def get_mentor_doc(self, mentor_doc_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(MentorDoc, mentor_doc_id)
            return _row_to_dict(row) if row else None

    def remove_mentor_doc(self, mentor_id: str, mentor_doc_id: str) -> dict | None:
        with self._session() as db:
            row = (
                db.query(MentorDoc)
                .filter(MentorDoc.id == mentor_doc_id, MentorDoc.mentor_id == mentor_id)
                .first()
            )
            if row:
                data = _row_to_dict(row)
                db.delete(row)
                db.commit()
                return data
        return None

    def get_mentor_doc_file_data(self, doc_id: str) -> bytes | None:
        with self._session() as db:
            row = db.get(MentorDoc, doc_id)
            return row.file_data if row else None

    # ━━━━━━━━━━━━━━━━━━ Mentor basic docs ━━━━━━━━━━━━━━━
    def add_mentor_basic_doc(self, doc: dict):
        with self._session() as db:
            db.add(MentorBasicDoc(**{k: v for k, v in doc.items() if hasattr(MentorBasicDoc, k)}))
            db.commit()

    def get_mentor_basic_docs(self, mentor_id: str, query: str | None = None, limit: int | None = None) -> list[dict]:
        with self._session() as db:
            q = db.query(MentorBasicDoc).filter(MentorBasicDoc.mentor_id == mentor_id)
            if query:
                like = f"%{query.lower()}%"
                q = q.filter(
                    MentorBasicDoc.digest_title.ilike(like)
                    | MentorBasicDoc.digest_summary.ilike(like)
                    | MentorBasicDoc.filename.ilike(like)
                )
            q = q.order_by(MentorBasicDoc.uploaded_at.desc())
            if limit:
                q = q.limit(limit)
            return [_row_to_dict(r) for r in q.all()]

    def get_mentor_basic_doc(self, doc_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(MentorBasicDoc, doc_id)
            return _row_to_dict(row) if row else None

    def remove_mentor_basic_doc(self, mentor_id: str, doc_id: str) -> dict | None:
        with self._session() as db:
            row = (
                db.query(MentorBasicDoc)
                .filter(MentorBasicDoc.id == doc_id, MentorBasicDoc.mentor_id == mentor_id)
                .first()
            )
            if row:
                data = _row_to_dict(row)
                db.delete(row)
                db.commit()
                return data
        return None

    def get_mentor_basic_doc_file_data(self, doc_id: str) -> bytes | None:
        with self._session() as db:
            row = db.get(MentorBasicDoc, doc_id)
            return row.file_data if row else None

    def get_recent_chat_activity(self, mentor_id: str, hours: int = 24) -> list[dict]:
        cutoff = datetime.now(_KST) - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")

        with self._session() as db:
            students = (
                db.query(User)
                .filter(User.role == "student", User.mentor_id == mentor_id)
                .all()
            )
            student_map = {s.id: s.name for s in students}
            if not student_map:
                return []

            sids = list(student_map.keys())

            messages = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id.in_(sids),
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= cutoff_str,
                )
                .order_by(ChatMessage.created_at)
                .all()
            )

            if not messages:
                return []

            # 한 번에 모든 assistant 메시지를 가져와서 N+1 제거
            assistant_msgs = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id.in_(sids),
                    ChatMessage.role == "assistant",
                    ChatMessage.created_at >= cutoff_str,
                )
                .order_by(ChatMessage.created_at)
                .all()
            )

            # user_id 별로 assistant 메시지를 시간순 정렬된 리스트로 그룹핑
            from collections import defaultdict
            assistant_by_user: dict[str, list] = defaultdict(list)
            for a in assistant_msgs:
                assistant_by_user[a.user_id].append(a)

            items = []
            for msg in messages:
                # 이진 탐색 대신 간단 순회: 해당 user 의 assistant 중 msg 이후 첫 번째
                metadata = {}
                for a in assistant_by_user.get(msg.user_id, []):
                    if a.created_at > msg.created_at:
                        metadata = (a.metadata_ or {})
                        break

                sent_materials = [
                    item.get("digest_title") or item.get("title") or item.get("filename")
                    for item in metadata.get("related_materials", [])
                ]
                sent_materials.extend(
                    item.get("title")
                    for item in metadata.get("curation_items", [])
                    if item.get("title")
                )

                items.append({
                    "student_id": msg.user_id,
                    "student_name": student_map.get(msg.user_id, msg.user_id),
                    "timestamp": msg.created_at,
                    "question": (msg.content or "")[:120],
                    "sent_materials": sent_materials[:6],
                })

            return sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)

    # ━━━━━━━━━━━━━━━━━━━ Curation ━━━━━━━━━━━━━━━━━━━━━━━
    def add_curation(self, item: dict):
        with self._session() as db:
            db.add(CurationItem(**{k: v for k, v in item.items() if hasattr(CurationItem, k)}))
            db.commit()

    def get_curations(self, category: str | None = None, date: str | None = None, limit: int | None = None) -> list[dict]:
        with self._session() as db:
            q = db.query(CurationItem)
            if category:
                q = q.filter(CurationItem.category == category)
            if date:
                q = q.filter(CurationItem.date == date)
            q = q.order_by(CurationItem.date.desc())
            if limit:
                q = q.limit(limit)
            rows = q.all()
            return [_row_to_dict(r) for r in rows]

    @property
    def curation_items(self) -> list[dict]:
        """기존 store.curation_items 직접 접근 호환용 property."""
        return self.get_curations()

    def get_curation_by_id(self, item_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(CurationItem, item_id)
            return _row_to_dict(row) if row else None

    def update_curation(self, item_id: str, updates: dict) -> dict | None:
        with self._session() as db:
            row = db.get(CurationItem, item_id)
            if not row:
                return None
            for k, v in updates.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            db.commit()
            db.refresh(row)
            return _row_to_dict(row)

    def remove_curation(self, item_id: str) -> dict | None:
        with self._session() as db:
            row = db.get(CurationItem, item_id)
            if row:
                data = _row_to_dict(row)
                db.delete(row)
                db.commit()
                return data
        return None

    # ━━━━━━━━━━━━━━━━━━━ 시드 (최초 1회) ━━━━━━━━━━━━━━━━
    def _seed_if_empty(self):
        with self._session() as db:
            if db.query(User).first():
                return
        self._seed()

    def _seed(self):
        now = datetime.now()
        admin_id = "admin_001"
        mentor_id = "mentor_001"
        ta1_id = "ta_jung"
        ta2_id = "ta_han"
        s1, s2, s3 = "student_001", "student_002", "student_003"
        invite = "KITKDT2026"

        users = [
            {"id": admin_id, "kakao_id": None, "name": "최관리자",
             "profile_image": "", "role": "admin",
             "mentor_id": None, "invite_code": None,
             "career_pref": None, "created_at": _now()},
            {"id": mentor_id, "kakao_id": None, "name": "이강민",
             "profile_image": "", "role": "mentor",
             "mentor_id": None, "invite_code": invite,
             "career_pref": None, "created_at": _now()},
            {"id": ta1_id, "kakao_id": None, "name": "정우성",
             "profile_image": "", "role": "ta",
             "mentor_id": None, "invite_code": None,
             "career_pref": None, "created_at": _now()},
            {"id": ta2_id, "kakao_id": None, "name": "한소희",
             "profile_image": "", "role": "ta",
             "mentor_id": None, "invite_code": None,
             "career_pref": None, "created_at": _now()},
            {"id": s1, "kakao_id": None, "name": "김민수",
             "profile_image": "", "role": "student",
             "mentor_id": mentor_id, "invite_code": None,
             "career_pref": "백엔드 개발", "created_at": _now()},
            {"id": s2, "kakao_id": None, "name": "이서연",
             "profile_image": "", "role": "student",
             "mentor_id": mentor_id, "invite_code": None,
             "career_pref": "프론트엔드 개발", "created_at": _now()},
            {"id": s3, "kakao_id": None, "name": "박지훈",
             "profile_image": "", "role": "student",
             "mentor_id": mentor_id, "invite_code": None,
             "career_pref": "데이터 엔지니어", "created_at": _now()},
        ]

        for u in users:
            self.create_user(u)

        self.set_invite_code(invite, mentor_id)

        # TA 스케줄
        td = now.strftime("%Y-%m-%d")
        tm = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        slots = [
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": td, "start_time": "10:00", "end_time": "11:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None, "slot_type": "available"},
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": tm, "start_time": "10:00", "end_time": "11:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None, "slot_type": "available"},
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": tm, "start_time": "11:00", "end_time": "12:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None, "slot_type": "available"},
            {"id": _uid(), "ta_id": ta2_id, "ta_name": "한소희 조교",
             "date": td, "start_time": "13:00", "end_time": "14:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None, "slot_type": "available"},
            {"id": _uid(), "ta_id": ta2_id, "ta_name": "한소희 조교",
             "date": tm, "start_time": "15:00", "end_time": "16:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None, "slot_type": "available"},
        ]
        self.add_ta_slots(slots)


# 싱글턴
store = Store()
