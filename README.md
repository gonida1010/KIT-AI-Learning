# Edu-Sync AI v3.0

> KDT 멀티 에이전트 하이브리드 멘토링 플랫폼

AI 챗봇, RAG 지식 검색, 일정 큐레이션, 조교 예약 시스템을 통합한 KDT(K-Digital Training) 교육 지원 플랫폼입니다.

---

## 주요 기능

| 기능                   | 설명                                                                    |
| ---------------------- | ----------------------------------------------------------------------- |
| **멀티 에이전트 챗봇** | 질문 의도에 따라 Agent A(행정·커리어) / Agent B(학습·조교) 자동 라우팅  |
| **RAG 지식 검색**      | PDF 문서 → FAISS 벡터 인덱스 → 의미 기반 검색 + LLM 답변 생성           |
| **일정별 큐레이션**    | 요일별 자동 분류(월=채용정보, 화=IT뉴스…) + FAISS 시맨틱 검색           |
| **TA 보충수업 예약**   | 월간 달력 기반 스케줄 관리, 반복 슬롯 생성, AI 브리핑 리포트            |
| **멘토 대시보드**      | 통합 단일 페이지: 상담 큐, 큐레이션, 수강생 관리, PDF 업로드, 초대 코드 |
| **하이브리드 인증**    | 카카오 OAuth 2.0 + QR 로그인 + 초대 코드 + 데모 모드                    |

---

## 기술 스택

- **Backend**: FastAPI, Python 3.11+, LangChain, FAISS, OpenAI GPT-4o-mini
- **Frontend**: React 19, Vite, Tailwind CSS 3, Lucide React, Framer Motion
- **벡터 DB**: FAISS (knowledge + curation 이중 인덱스)
- **인증**: Kakao OAuth 2.0, 세션 토큰, QR 로그인

---

## 아키텍처

```
 수강생 (카카오톡)              수강생 (웹 챗봇)
      │                              │
      ▼                              ▼
 카카오 i 오픈빌더              React SPA :3000
      │                              │
      └──── POST /api/kakao/chat ────┘
                     │
             ┌───────▼────────┐
             │  FastAPI :5060  │
             │  ├─ chat.py    │──── 웹 챗봇 API
             │  ├─ kakao.py   │──── 카카오 스킬 서버
             │  ├─ auth.py    │──── OAuth / QR / 데모
             │  ├─ mentor.py  │──── 멘토 대시보드 API
             │  ├─ ta.py      │──── TA 스케줄 API
             │  ├─ knowledge  │──── PDF 업로드/관리
             │  └─ curation   │──── 큐레이션 CRUD
             │                │
             │  AI Services   │
             │  ├─ agent_router.py │── 멀티에이전트 분기
             │  ├─ agent_a.py │── 행정·커리어 RAG
             │  ├─ agent_b.py │── 학습·조교 예약
             │  ├─ rag.py     │── FAISS 벡터스토어
             │  └─ llm_provider │── OpenAI / 온프레미스
             └────────────────┘
```

---

## 프로젝트 구조

```
KIT-AI-Learning/
├── backend/
│   ├── main.py                 # FastAPI 앱 (lifespan에서 벡터스토어 자동 로드)
│   ├── requirements.txt
│   ├── .env                    # OPENAI_API_KEY 설정
│   ├── data/                   # PDF 문서 저장 폴더
│   ├── vectorstore/            # FAISS 지식 인덱스
│   ├── vectorstore_curation/   # FAISS 큐레이션 인덱스
│   ├── db/
│   │   └── store.py            # JSON 기반 데이터 저장소
│   ├── models/
│   │   └── schemas.py          # Pydantic 모델
│   ├── routers/
│   │   ├── auth.py             # 인증 (OAuth, QR, 데모)
│   │   ├── chat.py             # 웹 챗봇 API
│   │   ├── kakao.py            # 카카오톡 i 오픈빌더 웹훅
│   │   ├── mentor.py           # 멘토 API
│   │   ├── ta.py               # TA 스케줄 API (반복 슬롯 포함)
│   │   ├── knowledge.py        # PDF 업로드/관리
│   │   └── curation.py         # 큐레이션 데이터 CRUD
│   └── services/
│       ├── agent_router.py     # 멀티 에이전트 라우터
│       ├── agent_a.py          # 행정·커리어 에이전트 (RAG + 큐레이션)
│       ├── agent_b.py          # 학습·조교 에이전트 (예약 등)
│       ├── llm_provider.py     # LLM 추상화 (OpenAI / 온프레미스)
│       └── rag.py              # RAG + 벡터스토어 관리
└── frontend/
    ├── package.json
    ├── vite.config.js          # 프록시: :3000 → :5060
    ├── tailwind.config.js      # 커스텀 primary 블루 팔레트
    └── src/
        ├── App.jsx
        ├── index.css
        ├── contexts/AuthContext.jsx
        ├── components/
        │   ├── Layout.jsx
        │   └── Sidebar.jsx
        └── pages/
            ├── LoginPage.jsx       # 로그인 (카카오/QR/데모)
            ├── StudentChat.jsx     # 수강생 AI 챗봇
            ├── MentorDashboard.jsx # 멘토 통합 대시보드
            ├── TADashboard.jsx     # TA 달력 스케줄 관리
            └── KnowledgeBase.jsx   # 지식 베이스 (PDF 관리)
```

---

## 실행 방법

### 1. 환경변수 설정

```bash
# backend/.env
OPENAI_API_KEY=sk-proj-your-key-here

# (선택) 카카오 OAuth 사용 시
KAKAO_CLIENT_ID=your-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:3000
```

### 2. 백엔드 실행

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5060 --reload
```

서버 구동 시 `data/` 폴더의 PDF가 자동으로 FAISS 인덱스에 로드됩니다.

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

`http://localhost:3000` 접속 → Vite 프록시로 백엔드(`localhost:5060`)에 자동 연결

### 4. 데모 로그인

로그인 화면에서 **데모** 탭 → 수강생/멘토/TA 역할 선택 → 즉시 체험 가능

---

## PDF → AI 파이프라인

1. `data/` 폴더에 PDF 배치 또는 웹에서 업로드 (`/api/knowledge/upload`)
2. 서버 시작 시 `load_or_build_vectorstore()` → PyPDF로 텍스트 추출 → 청크 분할 → OpenAI Embeddings → FAISS 인덱스 저장
3. 학생 질문 → 에이전트 라우터 → Agent A/B → RAG 검색 → 관련 청크 + LLM 답변 생성

---

## 카카오톡 i 오픈빌더 연동 가이드

### 전체 흐름

```
[카카오톡 사용자] → [카카오 i 오픈빌더 스킬] → [백엔드 /api/kakao/chat] → [멀티 에이전트] → [응답]
```

### Step 1 — 공개 URL 확보

카카오 오픈빌더는 공개 HTTPS URL이 필요합니다.

| 방법        | 난이도 | 비용    | 설명                                        |
| ----------- | ------ | ------- | ------------------------------------------- |
| **ngrok**   | ⭐     | 무료    | `ngrok http 5060` → 임시 HTTPS URL (개발용) |
| **Railway** | ⭐⭐   | 무료~$5 | GitHub 연결 → 자동 배포                     |
| **Render**  | ⭐⭐   | 무료    | Python Web Service                          |

```bash
# ngrok 예시
ngrok http 5060
# → https://xxxx-xx-xx.ngrok-free.app
```

### Step 2 — 카카오톡 채널 생성

1. [카카오톡 채널 관리자센터](https://center-pf.kakao.com) → **새 채널 만들기**
2. 채널명: "Edu-Sync AI" (자유)
3. **공개** 설정

### Step 3 — 카카오 i 오픈빌더 설정

1. [카카오 i 오픈빌더](https://chatbot.kakao.com) → **새 봇 만들기** → 채널 연결
2. **스킬** 탭 → 스킬 생성:
   - 이름: `Edu-Sync AI`
   - URL: `https://your-domain.com/api/kakao/chat`
   - Method: `POST`
3. **시나리오** → **폴백 블록** → 봇 응답 → 스킬데이터 → 위 스킬 선택
4. **배포** → 실행

### Step 4 — 테스트

1. 카카오톡에서 채널 검색 → 채팅 시작
2. "취업 자료 좀요" → AI 응답 + QuickReply 제공
3. 웹 대시보드에서 멘토 대기열 확인

### 웹훅 요청/응답 형식

**요청** (카카오 → 서버):

```json
{
  "userRequest": {
    "utterance": "취업 정보 알려줘",
    "user": { "id": "kakao_user_id" }
  }
}
```

**응답** (서버 → 카카오):

```json
{
  "version": "2.0",
  "template": {
    "outputs": [{ "simpleText": { "text": "AI 응답 내용..." } }],
    "quickReplies": [
      {
        "label": "📄 포트폴리오",
        "action": "message",
        "messageText": "포트폴리오 양식"
      }
    ]
  }
}
```

### (선택) 카카오 OAuth 로그인

1. [Kakao Developers](https://developers.kakao.com) → 앱 등록
2. **카카오 로그인** 활성화 + Redirect URI 등록
3. `.env`에 `KAKAO_CLIENT_ID`, `KAKAO_REDIRECT_URI` 추가

---

## API 엔드포인트

| Method   | Endpoint                              | 설명                    |
| -------- | ------------------------------------- | ----------------------- |
| `POST`   | `/api/auth/demo`                      | 데모 로그인             |
| `POST`   | `/api/auth/qr/generate`               | QR 로그인 토큰 생성     |
| `GET`    | `/api/auth/qr/check`                  | QR 폴링 확인            |
| `POST`   | `/api/chat`                           | 웹 챗봇 (멀티 에이전트) |
| `POST`   | `/api/kakao/chat`                     | 카카오톡 웹훅           |
| `GET`    | `/api/ta/slots`                       | TA 슬롯 목록            |
| `POST`   | `/api/ta/slots/recurring`             | 반복 슬롯 일괄 생성     |
| `DELETE` | `/api/ta/slots/{id}`                  | 슬롯 삭제               |
| `GET`    | `/api/ta/briefing/{id}`               | AI 브리핑 리포트        |
| `GET`    | `/api/mentor/queue`                   | 상담 대기 큐            |
| `POST`   | `/api/mentor/queue/{id}/resolve`      | 상담 해결               |
| `POST`   | `/api/mentor/invite`                  | 초대 코드 생성          |
| `GET`    | `/api/mentor/students/by-mentor/{id}` | 멘토별 수강생           |
| `GET`    | `/api/mentor/student/{id}/timeline`   | 수강생 타임라인         |
| `GET`    | `/api/curation/today`                 | 오늘의 큐레이션         |
| `POST`   | `/api/curation`                       | 큐레이션 등록           |
| `POST`   | `/api/knowledge/upload`               | PDF 업로드              |
| `GET`    | `/api/knowledge/documents`            | 문서 목록               |
| `POST`   | `/api/knowledge/rebuild`              | 벡터스토어 재빌드       |
| `GET`    | `/api/health`                         | 서버 상태               |

---

## 큐레이션 일정

| 요일   | 카테고리              |
| ------ | --------------------- |
| 월요일 | 채용 정보             |
| 화요일 | IT 뉴스 / 기술 트렌드 |
| 수요일 | 자격증 / 공모전       |
| 목요일 | 학습 자료             |
| 금요일 | 주간 리뷰 / 종합      |

학원에서 PDF를 해당 요일에 업로드 → 시스템이 자동으로 FAISS 큐레이션 벡터스토어에 인덱싱 → 학생 질문에 시맨틱 검색으로 매칭

---

## 프로덕션 고려사항

| 현재 (데모)      | 프로덕션 권장          |
| ---------------- | ---------------------- |
| JSON File Store  | PostgreSQL + Redis     |
| FAISS (CPU)      | Pinecone / Weaviate    |
| GPT-4o-mini 단일 | 비용 최적화 모델 분기  |
| 단일 서버        | Docker Compose + Nginx |

---

## 라이선스

MIT License
