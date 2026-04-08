"""
In-memory 데이터 저장소 + JSON 파일 영속성.
데모용 — 프로덕션에서는 PostgreSQL + Redis 로 전환.
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
        # ── Auth ──
        self.users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.qr_sessions: dict[str, dict] = {}
        self.invite_codes: dict[str, str] = {}  # code -> mentor_id

        # ── Chat ──
        self.chat_logs: dict[str, list[dict]] = {}
        self.handoff_queue: list[dict] = []

        # ── Scheduling ──
        self.schedules: list[dict] = []

        # ── Knowledge & Curation ──
        self.knowledge_docs: list[dict] = []
        self.curation_items: list[dict] = []

        # ── Student tracking ──
        self.student_events: dict[str, list[dict]] = {}

        self._load()

    # ━━━━━━━━━━━━━━━━━━━━━━━ 영속성 ━━━━━━━━━━━━━━━━━━━━━━━
    def _load(self):
        if DATA_FILE.exists():
            try:
                d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self.users = d.get("users", {})
                self.sessions = d.get("sessions", {})
                self.qr_sessions = d.get("qr_sessions", {})
                self.invite_codes = d.get("invite_codes", {})
                self.chat_logs = d.get("chat_logs", {})
                self.handoff_queue = d.get("handoff_queue", [])
                self.schedules = d.get("schedules", [])
                self.knowledge_docs = d.get("knowledge_docs", [])
                self.curation_items = d.get("curation_items", [])
                self.student_events = d.get("student_events", {})
                if self.users:
                    return
            except Exception:
                pass
        self._seed()

    def _save(self):
        DATA_FILE.write_text(
            json.dumps(
                {
                    "users": self.users,
                    "sessions": self.sessions,
                    "qr_sessions": self.qr_sessions,
                    "invite_codes": self.invite_codes,
                    "chat_logs": self.chat_logs,
                    "handoff_queue": self.handoff_queue,
                    "schedules": self.schedules,
                    "knowledge_docs": self.knowledge_docs,
                    "curation_items": self.curation_items,
                    "student_events": self.student_events,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━ 시드 데이터 ━━━━━━━━━━━━━━━━━━
    def _seed(self):
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        mentor_id = "mentor_001"
        ta1_id = "ta_jung"
        ta2_id = "ta_han"
        s1, s2, s3 = "student_001", "student_002", "student_003"
        invite = "KITKDT2026"

        # ── Users ──
        self.users = {
            mentor_id: {
                "id": mentor_id, "kakao_id": None, "name": "이강민",
                "profile_image": "", "role": "mentor",
                "mentor_id": None, "invite_code": invite,
                "career_pref": None, "created_at": _now(),
            },
            ta1_id: {
                "id": ta1_id, "kakao_id": None, "name": "정우성",
                "profile_image": "", "role": "ta",
                "mentor_id": None, "invite_code": None,
                "career_pref": None, "created_at": _now(),
            },
            ta2_id: {
                "id": ta2_id, "kakao_id": None, "name": "한소희",
                "profile_image": "", "role": "ta",
                "mentor_id": None, "invite_code": None,
                "career_pref": None, "created_at": _now(),
            },
            s1: {
                "id": s1, "kakao_id": None, "name": "김민수",
                "profile_image": "", "role": "student",
                "mentor_id": mentor_id, "invite_code": None,
                "career_pref": "백엔드 개발", "created_at": _now(),
            },
            s2: {
                "id": s2, "kakao_id": None, "name": "이서연",
                "profile_image": "", "role": "student",
                "mentor_id": mentor_id, "invite_code": None,
                "career_pref": "프론트엔드 개발", "created_at": _now(),
            },
            s3: {
                "id": s3, "kakao_id": None, "name": "박지훈",
                "profile_image": "", "role": "student",
                "mentor_id": mentor_id, "invite_code": None,
                "career_pref": "데이터 엔지니어", "created_at": _now(),
            },
        }

        self.invite_codes = {invite: mentor_id}

        # ── Chat logs ──
        self.chat_logs = {
            s2: [
                {"id": _uid(), "user_id": s2, "channel": "web", "role": "user",
                 "agent_type": None, "content": "취업 자료 좀요",
                 "choices": None, "metadata": None,
                 "created_at": (yesterday + timedelta(hours=22)).isoformat(timespec="seconds")},
                {"id": _uid(), "user_id": s2, "channel": "web", "role": "assistant",
                 "agent_type": "agent_a",
                 "content": "어떤 취업 자료를 찾고 계신가요? 아래에서 선택해 주세요!",
                 "choices": [
                     {"label": "📄 포트폴리오 양식", "description": "프로젝트 정리용 템플릿"},
                     {"label": "📋 이번 달 채용 공고", "description": "4월 IT 기업 채용 리스트"},
                     {"label": "🎤 면접 기출문제", "description": "최근 면접 질문 모음"},
                 ],
                 "metadata": None,
                 "created_at": (yesterday + timedelta(hours=22, seconds=3)).isoformat(timespec="seconds")},
            ],
        }

        # ── Handoff queue ──
        self.handoff_queue = [
            {
                "id": _uid(), "student_id": s3, "student_name": "박지훈",
                "reason": "슬럼프 상담 요청",
                "last_message": "요즘 공부에 의욕이 없어요... 멘토님과 이야기하고 싶습니다.",
                "priority": "high", "status": "pending",
                "created_at": (yesterday + timedelta(hours=23, minutes=30)).isoformat(timespec="seconds"),
            },
            {
                "id": _uid(), "student_id": s2, "student_name": "이서연",
                "reason": "프로젝트 방향 상담",
                "last_message": "팀 프로젝트 주제를 정하고 싶은데 조언이 필요해요.",
                "priority": "medium", "status": "pending",
                "created_at": (yesterday + timedelta(hours=21)).isoformat(timespec="seconds"),
            },
        ]

        # ── TA 스케줄 ──
        td = now.strftime("%Y-%m-%d")
        tm = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        self.schedules = [
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": td, "start_time": "10:00", "end_time": "11:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": td, "start_time": "14:00", "end_time": "15:00",
             "is_available": False, "booked_by": s1, "booked_by_name": "김민수",
             "booking_description": "파이썬 클래스에서 self가 뭔지 모르겠어요",
             "briefing_report": {
                 "student_name": "김민수",
                 "search_history": "함수 매개변수, 클래스 기초",
                 "core_need": "객체지향 기초 (클래스 및 __init__ 이해)",
                 "ai_recommendation": "함수 파트부터 약점이 있으니, 일반 함수와 메서드 차이점을 시각적으로 비교해 주세요.",
             }},
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": tm, "start_time": "10:00", "end_time": "11:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_id": ta1_id, "ta_name": "정우성 조교",
             "date": tm, "start_time": "11:00", "end_time": "12:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_id": ta2_id, "ta_name": "한소희 조교",
             "date": td, "start_time": "13:00", "end_time": "14:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None},
            {"id": _uid(), "ta_id": ta2_id, "ta_name": "한소희 조교",
             "date": tm, "start_time": "15:00", "end_time": "16:00",
             "is_available": True, "booked_by": None, "booked_by_name": None,
             "booking_description": None, "briefing_report": None},
        ]

        # ── Student events ──
        self.student_events = {
            s1: [
                {"timestamp": (now - timedelta(days=3)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "함수 매개변수", "detail": "챗봇 검색"},
                {"timestamp": (now - timedelta(days=2)).isoformat(timespec="seconds"),
                 "event_type": "doc_access", "content": "Python 기초 교재.pdf", "detail": "챕터7 열람"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "클래스 self", "detail": "챗봇 검색"},
                {"timestamp": (now - timedelta(hours=5)).isoformat(timespec="seconds"),
                 "event_type": "chat", "content": "self가 뭔지 모르겠어요", "detail": "AI 개념 설명"},
            ],
            s2: [
                {"timestamp": (now - timedelta(days=5)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "포트폴리오 작성법", "detail": "챗봇 검색"},
                {"timestamp": (now - timedelta(days=2)).isoformat(timespec="seconds"),
                 "event_type": "doc_access", "content": "이력서 작성 가이드.pdf", "detail": "전체 열람"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "chat", "content": "취업 자료 좀요", "detail": "AI 선택지 3개 제시"},
                {"timestamp": (now - timedelta(hours=8)).isoformat(timespec="seconds"),
                 "event_type": "curation_view", "content": "4월 채용정보 조회", "detail": "네이버·카카오 채용"},
            ],
            s3: [
                {"timestamp": (now - timedelta(days=7)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "슬럼프 극복", "detail": "챗봇 검색"},
                {"timestamp": (now - timedelta(days=3)).isoformat(timespec="seconds"),
                 "event_type": "search", "content": "자격증 종류", "detail": "챗봇 검색"},
                {"timestamp": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                 "event_type": "handoff", "content": "멘토 상담 요청", "detail": "슬럼프 상담"},
            ],
        }

        # ── Knowledge docs (sample) ──
        self.knowledge_docs = []

        # ── 큐레이션 콘텐츠 (5주 분량) ──
        self.curation_items = self._build_curation_seed(now)

        self._save()

    # ── 큐레이션 시드 데이터 생성 (5주) ──────────────────
    @staticmethod
    def _build_curation_seed(now: datetime) -> list[dict]:
        items: list[dict] = []

        def _add(date: datetime, cat: str, title: str, summary: str, content: str, tags: list[str]):
            items.append({
                "id": uuid.uuid4().hex[:12],
                "category": cat,
                "title": title,
                "summary": summary,
                "content": content,
                "date": date.strftime("%Y-%m-%d"),
                "weekday": date.weekday(),
                "source_filename": f"{date.strftime('%Y%m%d')}_{cat.replace('·', '_')}.pdf",
                "tags": tags,
                "created_at": date.strftime("%Y-%m-%dT09:00:00"),
            })

        # ── Week -4 (now - 28~24 days) ──
        base = now - timedelta(days=28)
        mon = base - timedelta(days=base.weekday())  # 월요일

        _add(mon, "채용정보", "3월 첫째 주 IT 채용 브리핑 — 삼성SDS·카카오·네이버",
             "삼성SDS 상반기 공채, 카카오 백엔드 수시, 네이버 클라우드 인턴 모집",
             "■ 삼성SDS 2026 상반기 개발 직군 공개 채용\n"
             "  - 접수 마감: 4월 10일(금)\n"
             "  - 모집 분야: 클라우드 엔지니어, 백엔드(Java/Python), AI/ML\n"
             "  - 우대: 정보처리기사, AWS 자격증 보유자\n\n"
             "■ 카카오 백엔드 개발자 수시채용\n"
             "  - Python/Java 경력 무관, 코딩 테스트 + 기술면접 2단계\n"
             "  - 연봉 레인지: 4,000~5,500만원 (신입 기준)\n\n"
             "■ 네이버 클라우드 인턴십 프로그램 2기\n"
             "  - 6개월 유급 인턴, 정규직 전환률 70%\n"
             "  - 마감: 3월 25일, 지원서 + 포트폴리오 필수\n\n"
             "■ 쿠팡 데이터 엔지니어 Junior 채용\n"
             "  - SQL/Python 필수, Spark/Airflow 우대\n"
             "  - 마감: 3월 31일",
             ["삼성SDS", "카카오", "네이버", "쿠팡", "공채"])

        _add(mon + timedelta(days=1), "IT뉴스", "Apple Vision Pro 2세대 발표, 국내 출시 확정",
             "Apple Vision Pro 2세대 40% 경량화, 공간 컴퓨팅 교육 활용 기대",
             "Apple이 WWDC 2026에서 Vision Pro 2세대를 공개했습니다.\n\n"
             "주요 변경사항:\n"
             "- 무게 40% 경량화 (450g → 270g)\n"
             "- M4 Pro 칩 탑재, 배터리 5시간\n"
             "- 가격 $2,499 (1세대 대비 $1,000 인하)\n\n"
             "교육 분야 임팩트:\n"
             "- 공간 컴퓨팅 기반 원격 코딩 교육 가능성\n"
             "- 3D 시각화를 통한 데이터 구조 학습\n"
             "- 국내 XR 교육 시장 2026년 5조원 규모 전망",
             ["Apple", "VisionPro", "XR", "교육"])

        _add(mon + timedelta(days=2), "AI타임스", "OpenAI o3 모델 공개 — 코딩 벤치마크 새 기록",
             "o3가 HumanEval 96.8% 달성, 멀티 에이전트 시스템으로 진화",
             "OpenAI가 o3 모델을 공개하며 코드 생성 정확도를 대폭 향상시켰습니다.\n\n"
             "벤치마크 성적:\n"
             "- HumanEval: 96.8% (o1 대비 +5.2%p)\n"
             "- SWE-bench: 68.3% (실제 GitHub 이슈 해결)\n"
             "- MATH: 98.1%\n\n"
             "핵심 변화:\n"
             "- '생각하는 시간(thinking time)' 조절 가능\n"
             "- 자동 코드 리뷰, 테스트 코드 생성, 리팩토링 제안\n"
             "- 멀티 에이전트 워크플로우 네이티브 지원\n\n"
             "국내 영향:\n"
             "- AI 코딩 어시스턴트 생산성 30% 향상 전망\n"
             "- KDT 교육 과정에 AI 도구 활용 커리큘럼 확대",
             ["OpenAI", "o3", "코딩", "에이전트"])

        _add(mon + timedelta(days=3), "자격증·공모전", "2026 상반기 정보처리기사 실기 접수 시작",
             "시험일 5/9, 접수 3/15~21, KDT 수강생 합격률 향상 팁 제공",
             "■ 2026년 상반기 정보처리기사 실기\n"
             "  - 시험일: 2026년 5월 9일(토)\n"
             "  - 접수 기간: 3월 15일 ~ 3월 21일\n"
             "  - 합격 기준: 60점 이상\n\n"
             "KDT 수강생 합격 팁:\n"
             "1. SQL 실기 문제 비중 높아짐 (40%)\n"
             "2. Python 코드 작성 문제 신설\n"
             "3. UML 다이어그램 필수 출제\n"
             "4. 네트워크/보안 이론 꾸준히 암기\n"
             "5. 기출 반복 + 핵심 키워드 정리\n\n"
             "■ 정보보안기사 시험 일정 (참고)\n"
             "  - 필기: 4월 26일, 실기: 7월 5일",
             ["정보처리기사", "자격증", "시험"])

        _add(mon + timedelta(days=4), "개발트렌드", "Rust가 Linux 커널에 본격 편입 — 시스템 프로그래밍의 미래",
             "Rust for Linux 6.x 정식 포함, 메모리 안전성 혁신",
             "Linux 6.x 커널에 Rust가 공식 편입되었습니다.\n\n"
             "왜 중요한가:\n"
             "- C 언어의 메모리 취약점(Buffer Overflow 등)을 원천 차단\n"
             "- Linux 커널 드라이버를 Rust로 작성 가능\n"
             "- Google, Microsoft, Amazon이 Rust 투자 확대\n\n"
             "Rust 학습 로드맵:\n"
             "1. The Rust Book (공식 문서)\n"
             "2. Rust by Example\n"
             "3. Exercism Rust Track\n"
             "4. 소규모 CLI 프로젝트 → 시스템 프로젝트\n\n"
             "추천 자료: 'Programming Rust, 2nd Edition'",
             ["Rust", "Linux", "시스템프로그래밍"])

        # ── Week -3 ──
        mon2 = mon + timedelta(weeks=1)

        _add(mon2, "채용정보", "중견 IT 기업 집중 채용 시즌 — LG CNS·토스·배민",
             "LG CNS DX 컨설턴트, 토스 프론트엔드, 배달의민족 백엔드 인턴 모집",
             "■ LG CNS DX 컨설턴트 신입 모집\n"
             "  - 마감: 4월 5일, 전공 무관\n"
             "  - IT 컨설팅 + 개발 하이브리드 포지션\n\n"
             "■ 토스 프론트엔드 개발자\n"
             "  - React/TypeScript 필수, 연봉 5,000만원~\n"
             "  - 코딩테스트 → 과제 → 기술면접 → 컬처핏\n\n"
             "■ 우아한형제들 백엔드 인턴\n"
             "  - 마감: 3월 28일, Java/Spring 우대\n"
             "  - 3개월 인턴 후 정규직 전환 심사\n\n"
             "■ NHN 클라우드 엔지니어\n"
             "  - 마감: 4월 15일, Linux/Docker 경험 우대",
             ["LG CNS", "토스", "배달의민족", "NHN"])

        _add(mon2 + timedelta(days=1), "IT뉴스", "글로벌 클라우드 시장 점유율 대변동 — GCP 급성장",
             "AWS 30%, Azure 25%, GCP 15%. 국내 클라우드 전환율 78% 돌파",
             "2026년 1분기 글로벌 클라우드 인프라 시장 리포트:\n\n"
             "시장 점유율:\n"
             "- AWS: 30% (전년 대비 -2%p)\n"
             "- Azure: 25% (+1%p)\n"
             "- GCP: 15% (+3%p) ← 가장 빠른 성장\n\n"
             "국내 동향:\n"
             "- 기업 클라우드 전환율 78% (2025년 65%에서 상승)\n"
             "- 멀티 클라우드 전략 채택 기업 63%\n"
             "- 네이버 클라우드, 국내 공공기관 점유율 1위\n\n"
             "취업 시사점:\n"
             "- 클라우드 관련 자격증(AWS SAA, GCP ACE) 수요 증가\n"
             "- DevOps/SRE 직군 채용 공고 전년 대비 40% 증가",
             ["클라우드", "AWS", "GCP", "Azure"])

        _add(mon2 + timedelta(days=2), "AI타임스", "On-device AI 시대 개막 — 스마트폰에서 LLM 실행",
             "삼성 S26 LLM 탑재, Apple Intelligence 2.0 국내 지원",
             "모바일 AI의 새 시대가 열렸습니다.\n\n"
             "■ 삼성 갤럭시 S26\n"
             "  - 7B 파라미터 sLLM 온디바이스 실행\n"
             "  - 실시간 번역, 문서 요약, 코드 해설 가능\n\n"
             "■ Apple Intelligence 2.0\n"
             "  - 한국어 공식 지원 시작\n"
             "  - Siri가 앱 간 컨텍스트를 이해하고 연동\n\n"
             "기술 트렌드:\n"
             "- 모델 경량화: Quantization(INT4), Pruning, Distillation\n"
             "- 프라이버시 강화: 데이터가 기기 밖으로 나가지 않음\n"
             "- 개발자 기회: CoreML, Samsung One UI AI SDK",
             ["온디바이스", "삼성", "Apple", "sLLM"])

        _add(mon2 + timedelta(days=3), "자격증·공모전", "2026 공개SW 개발자대회 참가자 모집",
             "과기정통부 주최, 총 상금 5천만원, AI 활용 부문 신설",
             "■ 2026 공개SW 개발자대회\n"
             "  - 주최: 과학기술정보통신부\n"
             "  - 후원: 네이버, 카카오, 삼성전자\n"
             "  - 접수: 3/20 ~ 4/10\n"
             "  - 총 상금: 5,000만원 (대상 1,000만원)\n\n"
             "부문:\n"
             "  1. 일반 부문 — 오픈소스 활용 서비스 개발\n"
             "  2. AI 활용 부문 (신설) — LLM/CV 기반 프로젝트\n"
             "  3. 학생 부문 — KDT/대학 재학생\n\n"
             "팀 구성: 1~4인, 팀 프로젝트 출품 가능\n"
             "심사: 기술성 40% + 완성도 30% + 활용성 30%",
             ["공모전", "오픈소스", "AI", "해커톤"])

        _add(mon2 + timedelta(days=4), "개발트렌드", "Next.js 15 App Router 완전 안정화 + Turbopack 정식 도입",
             "Server Components 본격화, 빌드 50% 개선, React 19 시너지",
             "Next.js 15가 안정 버전으로 출시되며 App Router가 완전히 안정화되었습니다.\n\n"
             "주요 변경사항:\n"
             "- Turbopack이 정식 빌드 도구로 채택 (Webpack 대체)\n"
             "- 빌드 속도 50% 향상, HMR 10배 빠름\n"
             "- Server Components가 기본 렌더링 전략\n\n"
             "React 19 시너지:\n"
             "- use() 훅으로 서버 데이터 직접 consume\n"
             "- 서버 액션(Server Actions) 폼 처리 간소화\n"
             "- Suspense + Streaming SSR 완전 지원\n\n"
             "실무 체크포인트:\n"
             "- pages/ → app/ 마이그레이션 가이드\n"
             "- 새 캐싱 전략 (fetch cache, revalidate)\n"
             "- Middleware를 활용한 인증 패턴",
             ["Next.js", "React", "Turbopack", "프론트엔드"])

        # ── Week -2 ──
        mon3 = mon + timedelta(weeks=2)

        _add(mon3, "채용정보", "스타트업 개발자 채용 총정리 — 당근·리디·뱅크샐러드·직방",
             "당근마켓 시니어/주니어 동시 채용, 리디 AI, 뱅크샐러드 분석가",
             "■ 당근마켓\n"
             "  - 시니어 백엔드 + 주니어 프론트엔드 동시 채용\n"
             "  - Go/Kotlin 기반, 대규모 트래픽 경험 우대\n\n"
             "■ 리디(RIDI) AI 엔지니어\n"
             "  - NLP 경험 우대, 추천 시스템 구축\n\n"
             "■ 뱅크샐러드 데이터 분석가 Junior\n"
             "  - SQL/Python 필수, 마감: 4/7\n\n"
             "■ 직방 풀스택 개발자 수시채용\n"
             "  - React + Node.js, 부동산 도메인",
             ["당근", "리디", "뱅크샐러드", "직방"])

        _add(mon3 + timedelta(days=1), "IT뉴스", "EU AI Act 2차 시행 — 국내 기업에 미치는 영향",
             "고위험 AI 분류 기준 확정, 국내 AI 윤리 가이드라인 도입 현황",
             "EU AI Act의 2차 시행이 개시되었습니다.\n\n"
             "핵심 내용:\n"
             "- 고위험 AI: 채용·교육·금융 분야 AI 시스템이 해당\n"
             "- 투명성 의무: AI가 생성한 콘텐츠에 라벨링 필수\n"
             "- 위반 시 과징금: 전 세계 매출의 최대 7%\n\n"
             "국내 영향:\n"
             "- 글로벌 서비스 기업은 EU 기준 준수 필수\n"
             "- 과기정통부 'AI 기본법' 시행령 준비 중\n"
             "- 주요 기업 AI 윤리 위원회 설립 트렌드\n\n"
             "개발자가 알아야 할 3가지:\n"
             "1. AI 모델 카드(Model Card) 작성법\n"
             "2. 편향성 테스트 도구 활용\n"
             "3. 데이터 출처 추적(Data Provenance)",
             ["EU", "AI법", "윤리", "규제"])

        _add(mon3 + timedelta(days=2), "AI타임스", "멀티모달 AI 에이전트 전쟁 — Gemini 2.0 vs GPT-5",
             "Google Gemini 2.0과 GPT-5 스펙 비교, AI 에이전트 자율 수행 시대",
             "■ Google Gemini 2.0\n"
             "  - 200만 토큰 컨텍스트 윈도우\n"
             "  - 네이티브 이미지/오디오/비디오 생성\n"
             "  - Gemini Code Assist로 IDE 통합\n\n"
             "■ OpenAI GPT-5\n"
             "  - 추론 능력 대폭 향상 (PhD 수준 STEM)\n"
             "  - 실시간 웹 검색 + 코드 실행 통합\n"
             "  - ChatGPT Operator: 웹 자율 탐색 에이전트\n\n"
             "AI 코딩 도구 비교:\n"
             "  - Cursor: VSCode 기반, 에디터 내 AI 대화\n"
             "  - GitHub Copilot: 코드 완성 + Chat + Workspace\n"
             "  - Windsurf: Cascade 에이전트 멀티스텝 실행",
             ["Gemini", "GPT-5", "에이전트", "코딩도구"])

        _add(mon3 + timedelta(days=3), "자격증·공모전", "SQLD 자격증 완벽 가이드 — 4/18 시험 대비",
             "2026 상반기 SQLD 시험일 4/18, SQL 학습 순서 & 합격 전략",
             "■ 2026 상반기 SQLD\n"
             "  - 시험일: 4월 18일(토)\n"
             "  - 접수: 3/25 ~ 3/31\n"
             "  - 합격 커트라인: 60점 (과목별 40점 이상)\n\n"
             "SQL 학습 순서:\n"
             "1. SELECT, WHERE, ORDER BY (기초)\n"
             "2. JOIN (INNER, LEFT, RIGHT, FULL)\n"
             "3. 서브쿼리 (스칼라, 인라인 뷰, EXISTS)\n"
             "4. GROUP BY, HAVING, 집계 함수\n"
             "5. 윈도우 함수 (ROW_NUMBER, RANK, LAG/LEAD)\n\n"
             "기출 분석:\n"
             "- 데이터 모델링 이론 20%\n"
             "- SQL 실무 40%\n"
             "- 최적화/인덱스 20%\n"
             "- 관리/보안 20%",
             ["SQLD", "SQL", "자격증"])

        _add(mon3 + timedelta(days=4), "개발트렌드", "WebAssembly + AI = 브라우저에서 LLM 실행",
             "Wasm으로 브라우저 내 LLM 실행 가능, WebGPU 표준화 진행",
             "브라우저에서 AI 모델을 직접 실행하는 시대가 다가왔습니다.\n\n"
             "WebAssembly(Wasm) + AI:\n"
             "- onnxruntime-web: 브라우저에서 ONNX 모델 추론\n"
             "- Transformers.js: HuggingFace 모델을 JS에서 사용\n"
             "- llama.cpp WASM 빌드: 3B 모델까지 브라우저 실행\n\n"
             "WebGPU:\n"
             "- Chrome 113+에서 기본 지원\n"
             "- GPU 가속 행렬 연산으로 추론 10x 가속\n\n"
             "WASI:\n"
             "- WebAssembly System Interface 2.0 프리뷰\n"
             "- 서버사이드 Wasm: Docker 대안으로 떠오름\n"
             "- Cloudflare Workers, Fastly Compute에서 이미 상용화",
             ["WebAssembly", "WebGPU", "AI", "브라우저"])

        # ── Week -1 ──
        mon4 = mon + timedelta(weeks=3)

        _add(mon4, "채용정보", "4월 공채 시즌 프리뷰 — SK텔레콤·현대오토에버·카카오뱅크",
             "SKT AI 사업부, 현대오토에버 DX, 카카오뱅크 보안개발자",
             "■ SK텔레콤 AI 사업부 신입\n"
             "  - 모집 예고: ~4/20 마감\n"
             "  - AI 플랫폼 개발, MLOps 엔지니어\n\n"
             "■ 현대오토에버 DX 개발자\n"
             "  - 마감: 4/15, 제조 도메인 경험 우대\n"
             "  - Java/Spring 기반 ERP/MES 시스템\n\n"
             "■ 카카오뱅크 보안 개발자 & 풀스택\n"
             "  - 마감: 4/12, 금융 도메인\n"
             "  - 정보보안기사 우대\n\n"
             "■ 라인플러스 글로벌 서비스 개발자\n"
             "  - 수시채용, 일본 근무 가능성",
             ["SKT", "현대오토에버", "카카오뱅크", "라인"])

        _add(mon4 + timedelta(days=1), "IT뉴스", "6G 기술 표준 경쟁 본격화 — 한국 특허 세계 2위",
             "삼성·LG 주도 6G 표준, 2030년 상용화 목표, 5G B2B 확대",
             "6G 글로벌 표준 경쟁이 본격화되고 있습니다.\n\n"
             "한국의 위치:\n"
             "- 6G 핵심 특허 출원 세계 2위 (1위 중국)\n"
             "- 삼성전자: 6G 핵심 칩셋 프로토타입 공개\n"
             "- LG전자: 테라헤르츠 대역 통신 실험 성공\n\n"
             "6G 핵심 사양 (예상):\n"
             "- 최대 속도: 1 Tbps (5G의 50배)\n"
             "- 지연시간: 0.1ms 이하\n"
             "- 동시 접속: 1km² 당 1,000만 대\n\n"
             "개발자 시사점:\n"
             "- 초저지연 통신 기반 실시간 AI 서비스\n"
             "- 디지털 트윈, 홀로그래픽 통신 새 시장",
             ["6G", "삼성", "LG", "통신"])

        _add(mon4 + timedelta(days=2), "AI타임스", "AI 코딩 어시스턴트 2026 벤치마크 리포트",
             "Copilot vs Cursor vs Cody 성능 비교, KDT 수강생 AI 도구 가이드",
             "AI 코딩 어시스턴트 2026 성능 비교 리포트:\n\n"
             "■ GitHub Copilot (GPT-4o 기반)\n"
             "  - 코드 완성: ★★★★☆ (4.3/5)\n"
             "  - 디버깅: ★★★★☆ (4.1/5)\n"
             "  - Workspace 기능 우수\n\n"
             "■ Cursor (Claude + GPT 하이브리드)\n"
             "  - 코드 완성: ★★★★★ (4.7/5)\n"
             "  - 리팩토링: ★★★★★ (4.8/5)\n"
             "  - Composer 멀티파일 편집 강점\n\n"
             "■ Sourcegraph Cody\n"
             "  - 대형 코드베이스 이해: ★★★★★ (4.9/5)\n"
             "  - 맞춤 컨텍스트 제공 탁월\n\n"
             "KDT 수강생 활용 가이드:\n"
             "1. 먼저 스스로 작성 시도 → AI로 검증\n"
             "2. AI 코드를 반드시 이해하고 수정\n"
             "3. 코딩테스트에서는 AI 없이 풀기 연습",
             ["Copilot", "Cursor", "AI코딩", "도구비교"])

        _add(mon4 + timedelta(days=3), "자격증·공모전", "네이버 D2SF 해커톤 참가 안내",
             "주제 'AI로 일상 불편 해결', 4/19~20 네이버 1784, 우승 300만원",
             "■ 네이버 D2SF 해커톤 2026\n"
             "  - 주제: 'AI로 해결하는 일상의 불편함'\n"
             "  - 일시: 4/19(토) ~ 4/20(일) / 1박 2일\n"
             "  - 장소: 네이버 1784 (성남시 분당구)\n"
             "  - 참가비: 무료, 식사 제공\n\n"
             "혜택:\n"
             "  - 참가자 전원: 1인 20만원 활동 지원금\n"
             "  - 대상: 300만원 + 네이버 인턴십 기회\n"
             "  - 우수상: 100만원\n\n"
             "참가 조건:\n"
             "  - 1~4인 팀, 개인 참가도 가능\n"
             "  - 재학생/수강생/졸업생 모두 가능\n"
             "  - 기획서 사전 제출: ~4/14",
             ["네이버", "해커톤", "D2SF"])

        _add(mon4 + timedelta(days=4), "개발트렌드", "TypeScript 6.0과 타입 시스템의 진화",
             "Decorators 5단계, Pattern Matching 제안, Biome vs ESLint",
             "TypeScript 6.0이 RC(릴리스 후보)를 공개했습니다.\n\n"
             "주요 신기능:\n"
             "- Decorators Stage 5: 클래스/메서드 데코레이터 정식 지원\n"
             "- 향상된 타입 추론: satisfies 키워드 활용 범위 확대\n"
             "- using 키워드: 리소스 자동 해제 패턴\n"
             "- Pattern Matching 제안 (TC39 Stage 2)\n\n"
             "린터/포매터:\n"
             "- Biome (Rust 기반): ESLint+Prettier 대체\n"
             "  속도 100배, 설정 간소화\n"
             "- ESLint v9: Flat Config 전면 도입\n\n"
             "2026 프론트엔드 필수 기술스택:\n"
             "TypeScript + React 19 + Next.js 15 + Tailwind v4 + Zustand/Jotai",
             ["TypeScript", "Biome", "프론트엔드"])

        # ── Current week (partial) ──
        # 4/6 Mon
        today = now
        this_mon = today - timedelta(days=today.weekday())

        _add(this_mon, "채용정보", "4월 첫째 주 채용 시장 동향 — 네이버웹툰·크래프톤·토스",
             "네이버웹툰 AI 10명 대규모 채용, 크래프톤 서버, 토스 시큐리티",
             "■ 네이버 웹툰 AI 개발자 (10명 대규모)\n"
             "  - 마감: 4/30\n"
             "  - AI 기반 웹툰 생성, 번역, 추천 시스템\n"
             "  - Python, PyTorch 필수\n\n"
             "■ 크래프톤 게임 서버 개발자\n"
             "  - 마감: 4/25\n"
             "  - C++/Go 기반 대규모 동시접속 서버\n"
             "  - 배틀그라운드 팀 배정 가능\n\n"
             "■ 비바리퍼블리카(토스) 시큐리티 엔지니어\n"
             "  - 마감: 4/18\n"
             "  - 금융 보안, 침투 테스트 경험 우대\n\n"
             "■ [KDT 연계] 4월 취업 특강\n"
             "  - 4/12(토) 14:00 '개발자 이력서 클리닉'\n"
             "  - 4/19(토) 14:00 '기술면접 실전 모의'\n"
             "  - 참석자: 학원 수강생 무료",
             ["네이버웹툰", "크래프톤", "토스", "특강"])

        if this_mon + timedelta(days=1) <= today:
            _add(this_mon + timedelta(days=1), "IT뉴스",
                 "한국 디지털 정부 플랫폼 2.0 출범 — 개발자 기회 확대",
                 "공공 API 통합 포털 개편, 마이데이터 2.0 시행, 클라우드 네이티브 의무화",
                 "디지털 정부 플랫폼 2.0이 출범했습니다.\n\n"
                 "주요 변화:\n"
                 "- 공공 API 통합 포털 전면 개편\n"
                 "  → REST API + GraphQL 지원, 개발자 문서 개선\n"
                 "- 마이데이터 2.0: 금융·의료·교육 데이터 통합\n"
                 "  → 개인정보 자기결정권 강화\n"
                 "- 공공기관 클라우드 네이티브 전환 의무화\n"
                 "  → 컨테이너(K8s) 기반 서비스 구축\n\n"
                 "개발자 기회:\n"
                 "- 공공 SI → 클라우드 전환 프로젝트 급증\n"
                 "- Kubernetes, Terraform 수요 폭발\n"
                 "- 공공 데이터 활용 서비스 창업 기회",
                 ["디지털정부", "공공API", "마이데이터", "K8s"])

        if this_mon + timedelta(days=2) <= today:
            _add(this_mon + timedelta(days=2), "AI타임스",
                 "Anthropic Claude 5 공개 — 200K 컨텍스트, 기업용 에이전트 플랫폼",
                 "코드 이해도 대폭 개선, 멀티스텝 추론, 오픈소스 LLM 동향 비교",
                 "Anthropic이 Claude 5를 공개했습니다.\n\n"
                 "주요 사양:\n"
                 "- 200K 토큰 컨텍스트 윈도우 (Claude 3 대비 2배)\n"
                 "- 코드 이해/생성 벤치마크 1위 (SWE-bench 78%)\n"
                 "- 멀티스텝 추론 정확도 92%\n"
                 "- 환각(Hallucination) 비율 2.1% (업계 최저)\n\n"
                 "기업용 에이전트 플랫폼:\n"
                 "- Claude for Enterprise: SSO, 감사 로그, API 관리\n"
                 "- Tool Use: 외부 API 호출, DB 쿼리 에이전트\n"
                 "- MCP(Model Context Protocol) 생태계 확장\n\n"
                 "오픈소스 LLM 비교:\n"
                 "- Llama 4 (Meta): 405B, 무료 상업화\n"
                 "- Mistral Large 3: 유럽 기반, EU AI Act 준수\n"
                 "- Qwen 2.5 (Alibaba): 아시아 언어 강세",
                 ["Claude", "Anthropic", "에이전트", "LLM비교"])

        return items

    # ━━━━━━━━━━━━━━━━━━━━━━━ User CRUD ━━━━━━━━━━━━━━━━━━━
    def create_user(self, data: dict) -> dict:
        self.users[data["id"]] = data
        self._save()
        return data

    def get_user(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def get_user_by_kakao_id(self, kakao_id: str) -> dict | None:
        for u in self.users.values():
            if u.get("kakao_id") == kakao_id:
                return u
        return None

    def get_all_users(self) -> list[dict]:
        return list(self.users.values())

    def get_students_by_mentor(self, mentor_id: str) -> list[dict]:
        return [u for u in self.users.values()
                if u["role"] == "student" and u.get("mentor_id") == mentor_id]

    # ━━━━━━━━━━━━━━━━━━━━━━ Sessions ━━━━━━━━━━━━━━━━━━━━━
    def create_session(self, token: str, user_id: str, stype: str = "kakao"):
        self.sessions[token] = {"user_id": user_id, "type": stype, "created_at": _now()}
        self._save()
        return token

    def get_session(self, token: str) -> str | None:
        s = self.sessions.get(token)
        if s:
            return s["user_id"] if isinstance(s, dict) else s
        return None

    def delete_session(self, token: str):
        self.sessions.pop(token, None)
        self._save()

    # ━━━━━━━━━━━━━━━━━━━━━━ Chat logs ━━━━━━━━━━━━━━━━━━━━
    def add_message(self, user_id: str, msg: dict):
        if user_id not in self.chat_logs:
            self.chat_logs[user_id] = []
        self.chat_logs[user_id].append(msg)
        self._save()

    def get_conversation(self, user_id: str) -> list[dict]:
        return self.chat_logs.get(user_id, [])

    # ━━━━━━━━━━━━━━━━━━━━━ Handoff ━━━━━━━━━━━━━━━━━━━━━━━
    def add_handoff(self, item: dict):
        self.handoff_queue.append(item)
        self._save()

    def get_pending_handoffs(self) -> list[dict]:
        return [h for h in self.handoff_queue if h["status"] == "pending"]

    def resolve_handoff(self, hid: str) -> bool:
        for h in self.handoff_queue:
            if h["id"] == hid:
                h["status"] = "resolved"
                self._save()
                return True
        return False

    # ━━━━━━━━━━━━━━━━━━━━ TA Schedules ━━━━━━━━━━━━━━━━━━━
    def get_available_slots(self) -> list[dict]:
        return [s for s in self.schedules if s["is_available"]]

    def get_all_slots(self) -> list[dict]:
        return self.schedules

    def book_slot(self, slot_id, student_id, student_name, desc, briefing=None):
        for s in self.schedules:
            if s["id"] == slot_id and s["is_available"]:
                s.update(is_available=False, booked_by=student_id,
                         booked_by_name=student_name,
                         booking_description=desc, briefing_report=briefing)
                self._save()
                return s
        return None

    def get_booked_slots(self) -> list[dict]:
        return [s for s in self.schedules if not s["is_available"] and s.get("booked_by")]

    def add_ta_slot(self, slot: dict):
        self.schedules.append(slot)
        self._save()

    # ━━━━━━━━━━━━━━━━━━ Student events ━━━━━━━━━━━━━━━━━━━
    def add_event(self, user_id: str, event: dict):
        if user_id not in self.student_events:
            self.student_events[user_id] = []
        self.student_events[user_id].append(event)
        self._save()

    def get_student_events(self, user_id: str) -> list[dict]:
        return self.student_events.get(user_id, [])

    def get_student(self, sid: str) -> dict | None:
        return self.users.get(sid)

    def get_all_students(self) -> list[dict]:
        return [u for u in self.users.values() if u["role"] == "student"]

    # ━━━━━━━━━━━━━━━━━ Knowledge docs ━━━━━━━━━━━━━━━━━━━━
    def add_knowledge_doc(self, doc: dict):
        self.knowledge_docs.append(doc)
        self._save()

    def get_knowledge_docs(self) -> list[dict]:
        return self.knowledge_docs

    def remove_knowledge_doc(self, doc_id: str) -> bool:
        for i, d in enumerate(self.knowledge_docs):
            if d["id"] == doc_id:
                self.knowledge_docs.pop(i)
                self._save()
                return True
        return False

    # ━━━━━━━━━━━━━━━━━━ Curation ━━━━━━━━━━━━━━━━━━━━━━━━━
    def add_curation(self, item: dict):
        self.curation_items.append(item)
        self._save()

    def get_curations(self, category: str | None = None, date: str | None = None) -> list[dict]:
        items = self.curation_items
        if category:
            items = [i for i in items if i["category"] == category]
        if date:
            items = [i for i in items if i["date"] == date]
        return sorted(items, key=lambda x: x["date"], reverse=True)


# 싱글턴
store = Store()
