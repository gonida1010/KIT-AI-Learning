# Edu-Sync AI — KDT 하이브리드 관리 플랫폼 (카카오톡 실연동)

> 수강생은 **카카오톡 채널**로 AI 멘토와 24시간 대화하고,  
> 멘토·조교는 **웹 대시보드**에서 대기열·브리핑·스케줄을 관리합니다.

---

## 1. 핵심 아키텍처

```
 수강생 (카카오톡 앱)
      │
      ▼
 카카오 i 오픈빌더 ── Skill Server Webhook ──▶ POST /api/kakao/webhook
                                                      │
                                              ┌───────▼────────┐
                                              │  FastAPI :5060  │
                                              │  ├─ kakao.py    │◀── 카카오 스킬 서버
                                              │  ├─ mentor.py   │
                                              │  ├─ ta.py       │
                                              │  ├─ analyze.py  │
                                              │  └─ knowledge.py│
                                              │                 │
                                              │  AI Services    │
                                              │  ├─ ai_chat.py  │── GPT-4o-mini
                                              │  ├─ rag.py      │── FAISS 벡터스토어
                                              │  └─ briefing.py │
                                              └───────┬────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │  React 웹 SPA  │◀── 멘토/조교 전용
                                              │  (관리 대시보드) │    http://localhost:3000
                                              └────────────────┘
```

**수강생** → 카카오톡에서만 대화 (웹에 학생용 페이지 없음)  
**멘토/조교** → 웹 대시보드에서 대기열·브리핑·스케줄 관리

---

## 2. 핵심 기능

| #   | 기능                     | 사용자      | 설명                                                     |
| --- | ------------------------ | ----------- | -------------------------------------------------------- |
| 1   | **카카오톡 AI 멘토**     | 수강생      | 카카오톡 채널에서 24시간 AI 상담. QuickReply 선택지 제공 |
| 2   | **멘토 핸드오프**        | 수강생→멘토 | "멘토 상담 요청" 시 대기열 자동 등록                     |
| 3   | **출근 브리핑 대시보드** | 멘토        | 밤사이 AI 응대 내역 + 대기열 + 학생 타임라인             |
| 4   | **조교 스마트 스케줄링** | 수강생→조교 | 빈 시간 예약 + AI 브리핑 리포트 자동 생성                |
| 5   | **CurriMap AI**          | 관리자      | 코드/스크린샷 → 커리큘럼 위치 시각화                     |

---

## 3. 프로젝트 구조

```
KIT-AI-Learning/
├── backend/
│   ├── main.py                  # FastAPI 앱 + 라우터 등록
│   ├── requirements.txt
│   ├── .env                     # OPENAI_API_KEY
│   ├── routers/
│   │   ├── kakao.py             # ★ 카카오 Webhook 엔드포인트
│   │   ├── mentor.py            #   멘토 브리핑·대기열·타임라인
│   │   ├── ta.py                #   조교 스케줄·예약·브리핑
│   │   ├── analyze.py           #   CurriMap 코드 분석
│   │   └── knowledge.py         #   지식 베이스 관리
│   ├── services/
│   │   ├── ai_chat.py           #   LLM 채팅 응답 생성
│   │   ├── briefing.py          #   조교 브리핑 리포트
│   │   ├── analyze.py           #   코드 분석 + Vision OCR
│   │   └── rag.py               #   PDF → FAISS 벡터스토어
│   ├── models/schemas.py        # Pydantic 모델
│   ├── db/store.py              # JSON 영속 데이터 저장소
│   └── data/                    # 강의 계획서 PDF
│
├── frontend/                    # ★ 관리자(멘토/조교) 전용
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── MentorDashboard.jsx
│   │   │   ├── TADashboard.jsx
│   │   │   ├── CurriMap.jsx
│   │   │   └── KnowledgeBase.jsx
│   │   └── components/          # Sidebar, Layout, QueueList 등
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 4. API 엔드포인트

### 카카오 Webhook (★ 핵심)

| Method | Path                          | 설명                                       |
| ------ | ----------------------------- | ------------------------------------------ |
| `POST` | `/api/kakao/webhook`          | 메인 스킬 서버 — 모든 카카오톡 메시지 처리 |
| `POST` | `/api/kakao/webhook/schedule` | 조교 보충 수업 예약 스킬 블록              |

### 멘토

| Method | Path                                | 설명          |
| ------ | ----------------------------------- | ------------- |
| `GET`  | `/api/mentor/briefing`              | 출근 브리핑   |
| `GET`  | `/api/mentor/queue`                 | 상담 대기열   |
| `POST` | `/api/mentor/queue/{id}/resolve`    | 대기열 해결   |
| `GET`  | `/api/mentor/students`              | 전체 학생     |
| `GET`  | `/api/mentor/student/{id}/timeline` | 학생 타임라인 |

### 조교 · 지식 베이스 · CurriMap

| Method     | Path                            | 설명        |
| ---------- | ------------------------------- | ----------- |
| `GET/POST` | `/api/ta/slots`, `/api/ta/book` | 스케줄·예약 |
| `POST`     | `/api/knowledge/upload`         | 문서 업로드 |
| `POST`     | `/api/analyze`                  | 코드 분석   |

---

## 5. 시작하기

### 사전 요구사항

- Python 3.11+, Node.js 18+
- OpenAI API Key

### 1단계: 백엔드

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY=sk-proj-... 설정
python main.py   # → :5060
```

### 2단계: 프론트엔드 (관리자 대시보드)

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000
```

### 3단계: 카카오 채널 연동

아래 "배포 & 카카오톡 연동 가이드" 참조.

---

## 6. 카카오톡 연동 가이드 (배포 후 해야 할 일)

### 📌 Step 1 — 서버 배포

로컬에서는 카카오 오픈빌더가 webhook을 호출할 수 없습니다.  
아래 중 하나로 **공개 URL**을 확보하세요:

| 방법        | 난이도 | 비용    | 설명                                              |
| ----------- | ------ | ------- | ------------------------------------------------- |
| **ngrok**   | ⭐     | 무료    | `ngrok http 5060` → 임시 공개 URL (개발·테스트용) |
| **Railway** | ⭐⭐   | 무료~$5 | GitHub 연결 → 자동 배포                           |
| **Render**  | ⭐⭐   | 무료    | Python Web Service 생성                           |
| **AWS EC2** | ⭐⭐⭐ | $5~     | t3.micro + Nginx 리버스 프록시                    |

> 예: `https://your-server.railway.app`

### 📌 Step 2 — 카카오톡 채널 생성

1. [카카오톡 채널 관리자센터](https://center-pf.kakao.com) 접속
2. **새 채널 만들기** → 채널 이름: "Edu-Sync AI 멘토" (자유)
3. 채널을 **공개**로 설정

### 📌 Step 3 — 카카오 i 오픈빌더 설정

1. [카카오 i 오픈빌더](https://chatbot.kakao.com) 접속
2. **새 봇 만들기** → 위에서 만든 채널 연결
3. **스킬** 탭 → **스킬 생성**:
   - 스킬 이름: `AI 멘토 데스크`
   - URL: `https://your-server.com/api/kakao/webhook`
   - Method: POST
4. **시나리오** → **폴백 블록** 선택
5. 폴백 블록의 **봇 응답**에서 → 스킬데이터 → 위에서 만든 `AI 멘토 데스크` 스킬 선택
6. **(선택)** 보충 수업 예약 블록 추가:
   - 새 블록 생성 → 패턴 발화: "보충 수업", "조교 예약"
   - 봇 응답 → 스킬데이터 → URL: `/api/kakao/webhook/schedule`
7. **배포** 탭 → 배포 실행

### 📌 Step 4 — 테스트

1. 카카오톡에서 채널 검색 → 채팅 시작
2. "취업 자료 좀요" 입력 → AI가 선택지(QuickReply) 제공
3. "🙋‍♂️ 멘토 상담 요청" 탭 → 대기열 등록 확인
4. 웹 대시보드(`localhost:3000`)에서 멘토 대기열에 표시되는지 확인

---

## 7. 카카오 Webhook 응답 형식 (참고)

우리 서버는 카카오 i 오픈빌더의 **SkillResponse** 형식으로 응답합니다:

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      { "simpleText": { "text": "어떤 취업 자료를 찾고 계신가요?" } }
    ],
    "quickReplies": [
      {
        "label": "📄 포트폴리오 양식",
        "action": "message",
        "messageText": "📄 포트폴리오 양식"
      },
      {
        "label": "📋 채용 공고",
        "action": "message",
        "messageText": "📋 채용 공고"
      },
      {
        "label": "🙋‍♂️ 멘토 상담 요청",
        "action": "message",
        "messageText": "멘토님과 직접 상담하기"
      }
    ]
  }
}
```

---

## 8. 프로덕션 고려사항

| 현재 (데모)           | 프로덕션 권장             |
| --------------------- | ------------------------- |
| JSON File Store       | PostgreSQL + Redis        |
| FAISS (CPU)           | Pinecone / Weaviate       |
| GPT-4o-mini 단일 모델 | 비용 최적화 모델 분기     |
| 단일 서버             | Docker Compose + Nginx    |
| 인증 없음             | JWT + 역할 기반 접근 제어 |
