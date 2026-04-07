"""
In-memory 데이터 저장소 + JSON 파일 영속성.
데모용으로 설계 — 프로덕션에서는 PostgreSQL + Redis 사용 권장.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "app_data.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _uid() -> str:
    return uuid.uuid4().hex[:12]


class Store:
    def __init__(self):
        self.conversations: dict[str, list[dict]] = {}
        self.handoff_queue: list[dict] = []
        self.ta_slots: list[dict] = []
        self.knowledge_docs: list[dict] = []
        self.student_events: dict[str, list[dict]] = {}
        self.students: dict[str, dict] = {}
        self.users: dict[str, dict] = {}      # id -> user
        self.sessions: dict[str, str] = {}     # token -> user_id
        self._load()

    # ─── 영속성 ───────────────────────────────────────────
    def _load(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self.conversations = data.get("conversations", {})
                self.handoff_queue = data.get("handoff_queue", [])
                self.ta_slots = data.get("ta_slots", [])
                self.knowledge_docs = data.get("knowledge_docs", [])
                self.student_events = data.get("student_events", {})
                self.students = data.get("students", {})
                self.users = data.get("users", {})
                self.sessions = data.get("sessions", {})
                return
            except Exception:
                pass
        self._seed()

    def _save(self):
        DATA_FILE.write_text(
            json.dumps(
                {
                    "conversations": self.conversations,
                    "handoff_queue": self.handoff_queue,
                    "ta_slots": self.ta_slots,
                    "knowledge_docs": self.knowledge_docs,
                    "student_events": self.student_events,
                    "students": self.students,
                    "users": self.users,
                    "sessions": self.sessions,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # ─── 시드 데이터 ─────────────────────────────────────
    def _seed(self):
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        self.students = {
            "student_1": {"id": "student_1", "name": "김민수"},
            "student_2": {"id": "student_2", "name": "이서연"},
            "student_3": {"id": "student_3", "name": "박지훈"},
        }

        # 샘플 대화
        self.conversations = {
            "student_2": [
                {"id": _uid(), "student_id": "student_2", "role": "user",
                 "content": "취업 자료 좀요", "choices": None, "has_handoff": False,
                 "timestamp": (yesterday + timedelta(hours=22)).isoformat(timespec="seconds")},
                {"id": _uid(), "student_id": "student_2", "role": "assistant",
                 "content": "어떤 취업 자료를 찾고 계신가요? 아래에서 선택해 주세요!",
                 "choices": [
                     {"label": "📄 포트폴리오 양식", "description": "프로젝트 정리용 포트폴리오 템플릿"},
                     {"label": "📋 이번 달 채용 공고", "description": "4월 IT 기업 공개 채용 리스트"},
                     {"label": "🎤 면접 기출문제", "description": "최근 기출 면접 질문 모음"},
                 ],
                 "has_handoff": True,
                 "timestamp": (yesterday + timedelta(hours=22, minutes=0, seconds=3)).isoformat(timespec="seconds")},
            ],
        }

        # 핸드오프 대기열
        self.handoff_queue = [
            {
                "id": _uid(),
                "student_id": "student_3",
                "student_name": "박지훈",
                "reason": "슬럼프 상담 요청",
                "last_message": "요즘 공부에 의욕이 없어요... 멘토님과 이야기하고 싶습니다.",
                "priority": "high",
                "status": "pending",
                "created_at": (yesterday + timedelta(hours=23, minutes=30)).isoformat(timespec="seconds"),
            },
            {
                "id": _uid(),
                "student_id": "student_2",
                "student_name": "이서연",
                "reason": "프로젝트 방향 상담",
                "last_message": "팀 프로젝트 주제를 정하고 싶은데 조언이 필요해요.",
                "priority": "medium",
                "status": "pending",
                "created_at": (yesterday + timedelta(hours=21)).isoformat(timespec="seconds"),
            },
        ]

        # 조교 스케줄
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        self.ta_slots = [
            {"id": _uid(), "ta_name": "정우성 조교", "date": today_str,
             "start_time": "10:00", "end_time": "11:00", "is_available": True,
             "booked_by": None, "booked_by_name": None, "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_name": "정우성 조교", "date": today_str,
             "start_time": "14:00", "end_time": "15:00", "is_available": False,
             "booked_by": "student_1", "booked_by_name": "김민수",
             "booking_description": "파이썬 클래스에서 self가 뭔지 모르겠어요",
             "briefing_report": {
                 "student_name": "김민수",
                 "search_history": "함수 매개변수, 클래스 기초",
                 "core_need": "객체지향 기초 (클래스 생성 및 __init__ 메서드의 이해)",
                 "ai_recommendation": "학생이 함수 파트부터 약점이 있으니, 일반 함수와 메서드의 차이점부터 시각적으로 비교해 주는 것을 권장합니다.",
             }},
            {"id": _uid(), "ta_name": "정우성 조교", "date": tomorrow_str,
             "start_time": "10:00", "end_time": "11:00", "is_available": True,
             "booked_by": None, "booked_by_name": None, "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_name": "정우성 조교", "date": tomorrow_str,
             "start_time": "11:00", "end_time": "12:00", "is_available": True,
             "booked_by": None, "booked_by_name": None, "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_name": "한소희 조교", "date": today_str,
             "start_time": "13:00", "end_time": "14:00", "is_available": True,
             "booked_by": None, "booked_by_name": None, "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_name": "한소희 조교", "date": tomorrow_str,
             "start_time": "15:00", "end_time": "16:00", "is_available": True,
             "booked_by": None, "booked_by_name": None, "booking_description": None, "briefing_report": None},
        ]

        # 학생 이벤트 타임라인
        self.student_events = {
            "student_1": [
                {"timestamp": (now - timedelta(days=3)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "함수 매개변수", "detail": "챗봇에서 키워드 검색"},
                {"timestamp": (now - timedelta(days=2)).isoformat(timespec="seconds"),
                 "event_type": "doc_access", "content": "Python 기초 교재.pdf", "detail": "챕터 7: 함수 파트 열람"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "클래스 self", "detail": "챗봇에서 키워드 검색"},
                {"timestamp": (now - timedelta(hours=5)).isoformat(timespec="seconds"),
                 "event_type": "chat", "content": "파이썬 클래스에서 self가 뭔지 모르겠어요", "detail": "AI가 개념 설명 제공"},
            ],
            "student_2": [
                {"timestamp": (now - timedelta(days=5)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "포트폴리오 작성법", "detail": "챗봇에서 키워드 검색"},
                {"timestamp": (now - timedelta(days=2)).isoformat(timespec="seconds"),
                 "event_type": "doc_access", "content": "이력서 작성 가이드.pdf", "detail": "전체 문서 열람"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "chat", "content": "취업 자료 좀요", "detail": "AI가 선택지 3개 제시"},
            ],
            "student_3": [
                {"timestamp": (now - timedelta(days=7)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "슬럼프 극복", "detail": "챗봇에서 키워드 검색"},
                {"timestamp": (now - timedelta(days=3)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "자격증 종류", "detail": "챗봇에서 키워드 검색"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "handoff", "content": "멘토 상담 요청", "detail": "슬럼프 상담 요청 — 대기열 등록"},
            ],
        }

        self.knowledge_docs = []
        self._save()

    # ─── 대화 ────────────────────────────────────────────
    def add_message(self, student_id: str, msg: dict):
        if student_id not in self.conversations:
            self.conversations[student_id] = []
        self.conversations[student_id].append(msg)
        self._save()

    def get_conversation(self, student_id: str) -> list[dict]:
        return self.conversations.get(student_id, [])

    # ─── 핸드오프 ────────────────────────────────────────
    def add_handoff(self, item: dict):
        self.handoff_queue.append(item)
        self._save()

    def get_pending_handoffs(self) -> list[dict]:
        return [h for h in self.handoff_queue if h["status"] == "pending"]

    def resolve_handoff(self, handoff_id: str) -> bool:
        for h in self.handoff_queue:
            if h["id"] == handoff_id:
                h["status"] = "resolved"
                self._save()
                return True
        return False

    # ─── TA 스케줄 ───────────────────────────────────────
    def get_available_slots(self) -> list[dict]:
        return [s for s in self.ta_slots if s["is_available"]]

    def get_all_slots(self) -> list[dict]:
        return self.ta_slots

    def book_slot(self, slot_id: str, student_id: str, student_name: str,
                  description: str, briefing: dict | None = None) -> dict | None:
        for s in self.ta_slots:
            if s["id"] == slot_id and s["is_available"]:
                s["is_available"] = False
                s["booked_by"] = student_id
                s["booked_by_name"] = student_name
                s["booking_description"] = description
                s["briefing_report"] = briefing
                self._save()
                return s
        return None

    def get_booked_slots(self) -> list[dict]:
        return [s for s in self.ta_slots if not s["is_available"] and s["booked_by"]]

    def add_ta_slot(self, slot: dict):
        self.ta_slots.append(slot)
        self._save()

    # ─── 학생 이벤트 ─────────────────────────────────────
    def add_event(self, student_id: str, event: dict):
        if student_id not in self.student_events:
            self.student_events[student_id] = []
        self.student_events[student_id].append(event)
        self._save()

    def get_student_events(self, student_id: str) -> list[dict]:
        return self.student_events.get(student_id, [])

    def get_student(self, student_id: str) -> dict | None:
        return self.students.get(student_id)

    def get_all_students(self) -> list[dict]:
        return list(self.students.values())

    # ─── 지식 베이스 ─────────────────────────────────────
    def add_knowledge_doc(self, doc: dict):
        self.knowledge_docs.append(doc)
        self._save()

    def get_knowledge_docs(self) -> list[dict]:
        return self.knowledge_docs

    def remove_knowledge_doc(self, doc_id: str) -> bool:
        before = len(self.knowledge_docs)
        self.knowledge_docs = [d for d in self.knowledge_docs if d["id"] != doc_id]
        if len(self.knowledge_docs) < before:
            self._save()
            return True
        return False

    # ─── 사용자 (OAuth) ──────────────────────────────────
    def create_user(self, user: dict) -> dict:
        self.users[user["id"]] = user
        self._save()
        return user

    def get_user(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def get_user_by_kakao_id(self, kakao_id: str) -> dict | None:
        for u in self.users.values():
            if u.get("kakao_id") == kakao_id:
                return u
        return None

    def get_all_users(self) -> list[dict]:
        return list(self.users.values())

    # ─── 세션 ────────────────────────────────────────────
    def create_session(self, token: str, user_id: str):
        self.sessions[token] = user_id
        self._save()

    def get_session(self, token: str) -> str | None:
        return self.sessions.get(token)

    def delete_session(self, token: str):
        self.sessions.pop(token, None)
        self._save()


# 싱글턴
store = Store()
