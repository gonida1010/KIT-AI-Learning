# Edu-Sync AI

> **KDT(K-Digital Training) 교육 운영을 위한 멀티 에이전트 AI 학습 지원 시스템**

Edu-Sync AI는 국비지원 코딩 학원 운영에 필요한 학습 지원·행정 안내·조교 예약·멘토 상담을 하나의 AI 챗봇 인터페이스로 통합한 플랫폼입니다.
관리자·멘토·조교·수강생 4개 역할에 맞춘 전용 대시보드를 제공하며, 카카오 로그인과 웹 로그인을 모두 지원합니다.

---

## 주요 기능

### 멀티 에이전트 챗봇

| 에이전트         | 역할           | 핵심 기능                                                                       |
| ---------------- | -------------- | ------------------------------------------------------------------------------- |
| **Agent Router** | 의도 분류      | 수강생 메시지를 분석하여 적절한 에이전트로 라우팅                               |
| **Agent A**      | 행정·학습 자료 | RAG 기반 지식 검색, 큐레이션, 멘토 자료 송부, 멘토 상담 연결                    |
| **Agent B**      | 조교 스케줄러  | 보충수업 예약(날짜→시간→필요내용→확정), 학습 질문 번역, 브리핑 리포트 자동 생성 |

### 역할별 대시보드

- **수강생**: AI 챗봇, 오늘의 큐레이션, 학습 팁(최신/기초), 조교 예약, 1:1 멘토 상담 요청
- **멘토**: 수강생 활동 타임라인, 조교 연결 현황, 자료 업로드(최신/기초), 큐레이션 확인, 수강생 초대 링크, 1:1 상담 요청 알림
- **조교**: 월간 달력 스케줄 관리(챗봇/수동), 예약 현황·브리핑 리포트 확인
- **관리자**: 전체 큐레이션 관리(등록/수정/삭제), 멘토 대기열 확인

### 핵심 기술 흐름

- **RAG (Retrieval-Augmented Generation)**: 학원 공지·취업 자료는 FAISS 벡터스토어로 검색하여 LLM에 컨텍스트 주입
- **멘토 자료 관리**: 멘토별 최신 자료/기초 자료를 분리 저장, 각각 독립 벡터스토어로 검색
- **조교 예약 자동화**: 4단계 예약 플로우(날짜 선택→시간 선택→필요 내용 입력→예약 확정) + AI 브리핑 리포트 자동 생성
- **일간 큐레이션**: 관리자가 날짜별 IT뉴스·채용정보·자격증·개발트렌드를 등록, 수강생에게 요일별 자동 배포
- **카카오 채널 연동**: 카카오톡 챗봇 → 웹 챗봇 통합 인터페이스

---

## 기술 스택

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **LLM**: OpenAI GPT (LangChain 비동기 호출)
- **벡터 검색**: FAISS (faiss-cpu)
- **ORM / DB**: SQLAlchemy 2.0 + PostgreSQL
- **PDF 파싱**: pypdf
- **배포**: Render (Web Service)

### Frontend

- **Framework**: React 19 (Vite)
- **스타일링**: Tailwind CSS 4
- **아이콘**: Lucide React
- **애니메이션**: Framer Motion
- **빌드**: Vite → `frontend/dist/` (FastAPI에서 정적 서빙)

### 인프라

- **DB**: PostgreSQL (Render 호스팅)
- **배포**: Render 자동 배포 (GitHub main 브랜치 push 시)
- **인증**: 세션 토큰 기반 + 카카오 OAuth 2.0

---

## 프로젝트 구조

```
KIT-AI-Learning/
├── backend/
│   ├── main.py                  # FastAPI 앱 진입점, SPA 정적 서빙
│   ├── requirements.txt
│   ├── .env                     # 환경변수 (커밋 제외)
│   ├── db/
│   │   ├── models.py            # SQLAlchemy 모델 (12개 테이블)
│   │   └── store.py             # 데이터 액세스 레이어
│   ├── models/
│   │   └── schemas.py           # Pydantic 스키마
│   ├── routers/
│   │   ├── admin.py             # 큐레이션 CRUD, 대기열 관리
│   │   ├── auth.py              # 로그인/세션/초대코드
│   │   ├── chat.py              # 챗봇 API, 예약 플로우
│   │   ├── curation.py          # 큐레이션 조회
│   │   ├── kakao.py             # 카카오 채널 웹훅
│   │   ├── knowledge.py         # 공용 지식 벡터스토어
│   │   ├── mentor.py            # 멘토 자료 CRUD, 수강생 관리
│   │   └── ta.py                # 조교 스케줄 챗봇/수동 관리
│   ├── services/
│   │   ├── agent_a.py           # 행정·학습 에이전트
│   │   ├── agent_b.py           # 조교 스케줄러 에이전트
│   │   ├── agent_router.py      # 의도 분류 라우터
│   │   ├── llm_provider.py      # OpenAI LLM 래퍼
│   │   └── rag.py               # FAISS 벡터스토어 관리
│   ├── vectorstore/             # 공용 지식 FAISS 인덱스
│   ├── vectorstore_curation/    # 큐레이션 FAISS 인덱스
│   ├── vectorstore_mentor/      # 멘토별 최신 자료 FAISS
│   └── vectorstore_mentor_basic/# 멘토별 기초 자료 FAISS
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # 라우팅, 역할별 화면 분기
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx   # 인증 상태 관리
│   │   ├── pages/
│   │   │   ├── StudentChat.jsx   # 수강생 챗봇 화면
│   │   │   ├── MentorDashboard.jsx # 멘토 대시보드
│   │   │   ├── MentorStudents.jsx  # 수강생 관리
│   │   │   ├── KnowledgeBase.jsx   # 자료실 (최신/기초)
│   │   │   ├── TADashboard.jsx     # 조교 스케줄 관리
│   │   │   ├── AdminDashboard.jsx  # 관리자 큐레이션
│   │   │   └── LoginPage.jsx       # 로그인
│   │   └── components/
│   │       ├── Layout.jsx        # 사이드바 레이아웃
│   │       ├── Sidebar.jsx       # 역할별 메뉴
│   │       └── ...
│   └── dist/                    # 빌드 결과물 (정적 서빙)
└── README.md
```

---

## API 엔드포인트 요약

| 경로                         | 메서드 | 설명                               |
| ---------------------------- | ------ | ---------------------------------- |
| `/api/auth/login`            | POST   | 이메일/비밀번호 로그인             |
| `/api/auth/login/kakao`      | POST   | 카카오 OAuth 로그인                |
| `/api/chat`                  | POST   | 챗봇 메시지 (자동 에이전트 라우팅) |
| `/api/chat/tips`             | POST   | 학습 팁 조회 (최신/기초)           |
| `/api/chat/booking/dates`    | GET    | 예약 가능 날짜 목록                |
| `/api/chat/booking/slots`    | GET    | 특정 날짜 시간대 목록              |
| `/api/chat/booking/confirm`  | POST   | 예약 확정 + 브리핑 생성            |
| `/api/chat/handoff`          | POST   | 1:1 멘토 상담 요청                 |
| `/api/curation/today`        | GET    | 오늘의 큐레이션                    |
| `/api/admin/curations`       | CRUD   | 큐레이션 관리                      |
| `/api/mentor/knowledge/*`    | CRUD   | 최신 자료 관리                     |
| `/api/mentor/basic/*`        | CRUD   | 기초 자료 관리                     |
| `/api/ta/slots`              | GET    | 조교 스케줄 전체                   |
| `/api/ta/schedule-assistant` | POST   | 스케줄 챗봇 (자연어→일정)          |

---

## 환경 변수

| 변수명                | 설명                                     |
| --------------------- | ---------------------------------------- |
| `OPENAI_API_KEY`      | OpenAI API 키                            |
| `OPENAI_MODEL`        | 사용 모델 (예:`gpt-4o-mini`) |
| `LLM_PROVIDER`        | LLM 공급자 (`openai`)                    |
| `EMBEDDING_PROVIDER`  | 임베딩 공급자 (`openai`)                 |
| `DATABASE_URL`        | PostgreSQL 접속 URL                      |
| `KAKAO_REST_API_KEY`  | 카카오 REST API 키                       |
| `KAKAO_CLIENT_SECRET` | 카카오 Client Secret                     |
| `KAKAO_REDIRECT_URI`  | 카카오 OAuth 리다이렉트 URI              |
| `FRONTEND_URL`        | 프론트엔드 URL                           |
| `CORS_ALLOW_ORIGINS`  | CORS 허용 오리진                         |

---

## 로컬 실행

### 1. 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env 파일에 환경변수 설정
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

### 3. 프로덕션 빌드

```bash
cd frontend
npm run build
# backend에서 frontend/dist/ 를 정적 서빙
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## 데모 계정

| 역할   | ID          | 비밀번호    | 이름     |
| ------ | ----------- | ----------- | -------- |
| 관리자 | admin_001   | admin_001   | 최관리자 |
| 멘토   | mentor_001  | mentor_001  | 이강민   |
| 조교   | ta_jung     | ta_jung     | 정우성   |
| 조교   | ta_han      | ta_han      | 한소희   |
| 수강생 | student_001 | student_001 | 김민수   |
| 수강생 | student_002 | student_002 | 이서연   |
| 수강생 | student_003 | student_003 | 박지훈   |

---

## 배포

- **플랫폼**: Render (Web Service)
- **빌드 커맨드**: `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
- **시작 커맨드**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **라이브 URL**: https://kit-ai-learning.onrender.com

---

## 라이선스

이 프로젝트는 KIT 경진대회 출품용으로 제작되었습니다.
