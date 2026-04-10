# Edu-Sync AI

KDT 운영용 멀티 에이전트 학습 지원 시스템입니다. 현재 구현 기준으로 관리자, 멘토, 조교, 수강생 화면이 분리되어 있고, 업로드된 자료는 AI 요약과 벡터 검색 흐름에 연결됩니다.

## 빠른 시작

### 1. 저장소 준비

```powershell
git clone <your-repo-url>
cd c:\Pyg\Projects\KIT\KIT-AI-Learning
```

### 2. 백엔드 환경 준비

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 환경변수 설정

파일 경로: `backend/.env`

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
KAKAO_REST_API_KEY=...
KAKAO_CLIENT_SECRET=...
KAKAO_REDIRECT_URI=http://localhost:3000/oauth/callback
FRONTEND_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000
```

### 4. 백엔드 실행

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 5. 프론트엔드 실행

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend
npm install
npm run dev
```

### 6. 확인 주소

- 프론트엔드: `http://localhost:3000`
- 백엔드 헬스체크: `http://localhost:8001/api/health`

### 7. 자동 생성 항목

- `backend/db/app_data.json` 시드 데이터
- `backend/vectorstore` 공통 벡터 저장소
- `backend/vectorstore_curation` 큐레이션 벡터 저장소
- `backend/vectorstore_mentor/<mentor_id>` 멘토별 벡터 저장소

## 역할별 화면 요약

### 관리자

파일: `frontend/src/pages/AdminDashboard.jsx`

- 상단 카테고리 탭으로 큐레이션 주제 선택
- 날짜별 1건만 등록 가능한 예약형 큐레이션 운영
- 파일 드래그 업로드와 외부 링크 등록 지원
- 이미 등록된 날짜에 업로드 시 중앙 안내 효과로 차단
- 달력에서 날짜별 등록 여부와 카테고리를 색상으로 구분
- 달력 호버로 첨부 제목 확인
- 선택 날짜 자료 수정, 삭제, 첨부 열기 가능

### 멘토 대시보드

파일: `frontend/src/pages/MentorDashboard.jsx`

- 최근 24시간 질문 기록 확인
- 학생에게 송부된 자료 기록 확인
- 오늘 큐레이션 확인
- 내 최신 자료 5개 확인
- 대시보드에서 바로 자료 업로드

### 멘토 수강생 관리

파일: `frontend/src/pages/MentorStudents.jsx`

- 담당 수강생 목록 확인
- 수강생별 조교 연결 현황 확인
- 활동 타임라인은 최근 한 달 기준으로 5개씩 더보기
- 헤더 우측에서 수강생 초대 링크 생성 및 복사

### 멘토 자료소

파일: `frontend/src/pages/KnowledgeBase.jsx`

- 멘토 전용 파일 업로드
- 외부 링크 등록
- 최신 자료와 오래된 자료 분리 조회
- 첨부 열기 및 삭제

### 조교

파일: `frontend/src/pages/TADashboard.jsx`

- 월 단위 스케줄 챗봇으로 자연어 해석 후 확인 요청
- 수동 스케줄 설정 카드로 요일별 시간 직접 편집
- 미리보기와 바로 적용 지원
- 달력에서 휴무, 예약 가능 시간, 예약 건수 압축 표시
- 달력 호버로 하루 전체 시간 정보 확인
- 예약자 정보, 공부 내용, AI 브리핑 확인

### 수강생

파일: `frontend/src/pages/StudentChat.jsx`

- 웹 챗봇 대화
- 큐레이션 자료 추천
- 멘토 자료 추천
- 조교 예약 유도
- 멘토 연결 유도

## 백엔드 주요 구성

- `backend/main.py`: FastAPI 시작, LLM 및 벡터 저장소 초기화
- `backend/routers/chat.py`: 웹 챗봇
- `backend/routers/kakao.py`: 카카오 웹훅과 카카오 조교 예약 흐름
- `backend/routers/curation.py`: 큐레이션 등록, 수정, 삭제, 첨부 열기
- `backend/routers/mentor.py`: 멘토 대시보드, 학생 관리, 자료 등록, 조회, 삭제
- `backend/routers/ta.py`: 조교 슬롯 조회, 스케줄 보조, 예약 처리
- `backend/services/agent_router.py`: 멀티 에이전트 라우팅
- `backend/services/agent_a.py`: 취업, 행정, 큐레이션, 멘토 자료 응답
- `backend/services/agent_b.py`: 학습, 조교, 예약 응답
- `backend/services/rag.py`: 벡터 저장소 적재와 검색
- `backend/services/llm_provider.py`: LLM 연결 계층

## AI와 RAG 사용 범위

### LLM 사용 위치

- 질문 의도 분기: `backend/services/agent_router.py`
- 취업 및 행정 응답 생성: `backend/services/agent_a.py`
- 학습 및 조교 응답 생성: `backend/services/agent_b.py`
- 관리자 큐레이션 업로드 요약: `backend/routers/curation.py`
- 멘토 자료 업로드 요약: `backend/routers/mentor.py`
- 조교 예약 브리핑 생성: `backend/services/agent_b.py`
- 조교 스케줄 해석 및 요약: `backend/routers/ta.py`

### 벡터 저장소

- 공통 자료: `backend/vectorstore`
- 큐레이션 자료: `backend/vectorstore_curation`
- 멘토 전용 자료: `backend/vectorstore_mentor/<mentor_id>`

## 주요 동작 흐름

### 관리자 큐레이션

1. 관리자가 카테고리와 날짜를 정합니다.
2. 파일 또는 링크를 등록합니다.
3. 서버가 내용을 읽고 AI 요약을 생성합니다.
4. 메타데이터와 벡터 저장소에 함께 적재합니다.
5. 지정된 날짜에 멘토 대시보드와 챗봇에서 활용됩니다.

### 멘토 자료

1. 멘토가 대시보드 또는 자료소에서 파일이나 링크를 업로드합니다.
2. 서버가 제목과 요약을 AI로 생성합니다.
3. 멘토 전용 벡터 저장소에 적재합니다.
4. 수강생 질문 시 관련 자료를 검색해 응답에 포함합니다.

### 조교 스케줄

1. 조교가 자연어 또는 수동 설정으로 월간 스케줄을 작성합니다.
2. 시스템이 먼저 해석 결과를 요약해서 확인을 요청합니다.
3. 확인 후 실제 슬롯에 반영합니다.
4. 기존 예약 기록은 유지한 채 가능 시간과 휴무 규칙을 갱신합니다.

### 카카오 조교 예약

1. 학생이 카카오 메뉴에서 조교 보충 수업을 선택합니다.
2. 예약 가능한 시간이 Quick Reply로 노출됩니다.
3. 학생이 시간을 고르고 질문 내용을 입력합니다.
4. 서버가 AI 브리핑을 생성합니다.
5. 조교 대시보드에서 예약자, 시간, 요약, 브리핑을 확인합니다.

## 카카오 연동 준비 체크

직접 준비해야 하는 항목입니다.

1. Kakao Developers 앱 생성
2. REST API 키 발급
3. Redirect URI 등록
4. 카카오톡 채널 생성
5. 카카오 i 오픈빌더 봇 생성
6. 채널 연결
7. HTTPS 도메인 준비
8. 오픈빌더 스킬 URL 등록
9. 상시 메뉴 구성
10. 실제 채널 배포 후 테스트

### 1. Kakao Developers 앱 생성

1. `https://developers.kakao.com` 에 접속합니다.
2. 내 애플리케이션으로 이동합니다.
3. 애플리케이션 추가하기를 누릅니다.
4. 앱 이름과 회사명을 입력하고 앱을 생성합니다.
5. 생성 후 앱 설정 > 앱 키로 이동합니다.
6. 여기서 `REST API 키`를 복사합니다.

이 값은 아래 환경변수에 들어갑니다.

```env
KAKAO_REST_API_KEY=발급받은_REST_API_키
KAKAO_CLIENT_SECRET=플랫폼_키_설정에서_발급한_클라이언트_시크릿
```

### 2. 카카오 로그인 활성화

웹 로그인용 설정입니다. 현재 프로젝트는 [backend/routers/auth.py](backend/routers/auth.py) 기준으로 카카오 로그인 URL 생성과 콜백 처리를 합니다.

관련 API:

- `GET /api/auth/kakao/login-url`
- `POST /api/auth/kakao/callback`

설정 순서:

1. Kakao Developers에서 제품 설정 > 카카오 로그인으로 이동합니다.
2. 카카오 로그인을 활성화합니다.
3. Redirect URI를 등록합니다.
4. 동의항목에서 최소 프로필 닉네임 사용 여부를 확인합니다.

로컬 예시:

```env
KAKAO_CLIENT_SECRET=카카오_플랫폼_키_설정의_클라이언트_시크릿
KAKAO_REDIRECT_URI=http://localhost:3000/oauth/callback
```

운영 예시:

```env
KAKAO_CLIENT_SECRET=카카오_플랫폼_키_설정의_클라이언트_시크릿
KAKAO_REDIRECT_URI=https://your-frontend-domain.com/oauth/callback
```

### 3. 이 프로젝트에 넣어야 하는 환경변수

파일 위치: `backend/.env`

최소 권장 예시는 아래입니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
KAKAO_REST_API_KEY=발급받은_REST_API_키
KAKAO_CLIENT_SECRET=카카오_플랫폼_키_설정의_클라이언트_시크릿
KAKAO_REDIRECT_URI=http://localhost:3000/oauth/callback
FRONTEND_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000
```

운영 배포 시 예시는 아래처럼 바꿉니다.

```env
KAKAO_REST_API_KEY=발급받은_REST_API_키
KAKAO_CLIENT_SECRET=카카오_플랫폼_키_설정의_클라이언트_시크릿
KAKAO_REDIRECT_URI=https://your-frontend-domain.com/oauth/callback
FRONTEND_URL=https://your-frontend-domain.com
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
```

### 4. 카카오톡 채널 생성

1. 카카오톡 채널 관리자센터에 접속합니다.
2. 채널 만들기를 눌러 서비스 채널을 생성합니다.
3. 채널명, 검색용 아이디, 프로필 이미지를 설정합니다.
4. 추후 오픈빌더와 연결할 채널인지 확인합니다.

### 5. 카카오 i 오픈빌더 봇 생성

1. 카카오 i 오픈빌더에 접속합니다.
2. 새 봇 만들기를 선택합니다.
3. 챗봇 이름과 기본 설명을 입력합니다.
4. 이후 스킬 서버 연결 방식으로 설정합니다.

현재 프로젝트의 카카오 스킬 서버 라우트는 [backend/routers/kakao.py](backend/routers/kakao.py)입니다.

### 6. 채널과 오픈빌더 연결

1. 오픈빌더에서 만든 봇 설정 화면으로 이동합니다.
2. 카카오톡 채널 연결 메뉴를 찾습니다.
3. 위에서 만든 채널을 이 봇과 연결합니다.
4. 연결 후 테스트 채널에서 봇 응답이 가능한 상태로 둡니다.

### 7. HTTPS 도메인 준비

오픈빌더 스킬 URL은 실제 연결 시 HTTPS가 필요합니다. 선택지는 보통 아래 셋 중 하나입니다.

1. 실제 서버 도메인 배포
2. `ngrok` 사용
3. `cloudflared tunnel` 사용

로컬에서 임시 테스트만 하려면 예를 들어 `ngrok`을 쓸 수 있습니다.

```powershell
ngrok http 8001
```

그러면 예시 주소가 아래처럼 생성됩니다.

```text
https://abcd-1234.ngrok-free.app
```

이 도메인을 스킬 URL의 앞부분으로 사용하면 됩니다.

### 8. 오픈빌더 스킬 URL 등록

현재 이 프로젝트에서 실제 등록할 스킬 URL은 아래 3개입니다.

#### 메인 AI 대화 스킬

```text
POST /api/kakao/webhook
```

운영 예시:

```text
https://your-domain.com/api/kakao/webhook
```

역할:

- 일반 질의응답
- 멀티 에이전트 라우팅
- 멘토 상담 요청
- 예약 메시지 후속 처리

#### 조교 예약 스킬

```text
POST /api/kakao/webhook/schedule
```

운영 예시:

```text
https://your-domain.com/api/kakao/webhook/schedule
```

역할:

- 예약 가능한 조교 시간 Quick Reply 제공
- 조교 예약 시작점 제공

#### 큐레이션 조회 스킬

```text
POST /api/kakao/webhook/curation
```

운영 예시:

```text
https://your-domain.com/api/kakao/webhook/curation
```

카테고리별로 나누고 싶으면 query string을 함께 붙일 수 있습니다.

예시:

```text
https://your-domain.com/api/kakao/webhook/curation?category=채용정보,IT뉴스
https://your-domain.com/api/kakao/webhook/curation?category=자격증·공모전
```

### 오픈빌더 스킬 URL 예시

- 메인 AI: `https://your-domain.com/api/kakao/webhook`
- 큐레이션 조회: `https://your-domain.com/api/kakao/webhook/curation`
- 조교 예약: `https://your-domain.com/api/kakao/webhook/schedule`

### 9. 상시 메뉴 구성 예시

오픈빌더 또는 채널 메뉴에서 아래처럼 두면 됩니다.

1. 필요한 정보 채팅
   연결 스킬: 메인 AI 스킬
2. 조교 보충 수업
   연결 스킬: 조교 예약 스킬
3. 채용·IT뉴스 보기
   연결 스킬: 큐레이션 조회 스킬
   카테고리 예시: `채용정보,IT뉴스`
4. 자격증·공모전 보기
   연결 스킬: 큐레이션 조회 스킬
   카테고리 예시: `자격증·공모전`
5. 멘토 상담 요청
   메인 AI 스킬에서 Quick Reply 또는 발화 유도로 처리

### 10. 이 프로젝트에서 실제로 테스트해야 하는 입력 흐름

#### 메인 챗봇 테스트

1. 카카오톡 채널에서 일반 질문을 보냅니다.
2. [backend/routers/kakao.py](backend/routers/kakao.py)의 `/api/kakao/webhook` 이 응답하는지 확인합니다.
3. Quick Reply가 내려오는지 확인합니다.

#### 멘토 상담 요청 테스트

카카오톡에서 아래 중 하나를 보냅니다.

```text
멘토님과 직접 상담하기
멘토 상담 요청
```

기대 결과:

- handoff 큐 등록
- 카카오 응답 반환

#### 조교 예약 테스트

1. 카카오 메뉴에서 조교 보충 수업 진입
2. `/api/kakao/webhook/schedule` 이 예약 슬롯을 내려주는지 확인
3. Quick Reply 버튼 클릭
4. 아래 형식으로 입력

```text
예약정보:slot_id:홍길동 / 010-1234-5678 / 파이썬 클래스 self가 헷갈려요
```

5. 예약 완료 메시지가 오는지 확인
6. [frontend/src/pages/TADashboard.jsx](frontend/src/pages/TADashboard.jsx) 에 예약이 반영되는지 확인

#### 큐레이션 조회 테스트

1. 큐레이션 메뉴 진입
2. `/api/kakao/webhook/curation` 이 최신 큐레이션 5개를 내려주는지 확인
3. 카테고리별 스킬이면 category query string 필터가 적용되는지 확인

### 11. 배포 직전 최종 체크리스트

1. `backend/.env` 의 `KAKAO_REST_API_KEY` 입력 완료
2. `backend/.env` 의 `KAKAO_CLIENT_SECRET` 입력 완료 또는 카카오 콘솔에서 클라이언트 시크릿 비활성화
3. `backend/.env` 의 `KAKAO_REDIRECT_URI` 가 실제 프론트 주소와 일치
4. `CORS_ALLOW_ORIGINS` 에 실제 프론트 주소가 포함됨
5. 백엔드 HTTPS 주소가 외부에서 접근 가능
6. 오픈빌더 스킬 URL 3개가 모두 저장됨
7. 카카오톡 채널과 오픈빌더 봇 연결 완료
8. 일반 질의 테스트 완료
9. 멘토 상담 요청 테스트 완료
10. 조교 예약 Quick Reply 테스트 완료
11. 조교 대시보드 반영 테스트 완료
12. 큐레이션 조회 테스트 완료
13. 실제 채널 배포 후 최종 실사용 테스트 완료

## 운영 전 체크 포인트

- 토큰 전달은 query string 대신 `Authorization` 헤더 또는 HttpOnly cookie로 변경 권장
- 현재 JSON 저장소는 시연용이며 운영 전 PostgreSQL 권장
- 세션 및 임시 상태는 Redis 도입 권장
- 첨부 파일 MIME 검사, 파일 크기 제한, 악성 파일 검사 추가 권장
- 외부 링크 허용 도메인 정책과 redirect 검증 권장
- 카카오 로그인은 데모 시연용. 실제 학원 운영 시 학원 자체 인증 시스템에 연동하는 구조

---

## 배포 가이드 (Render)

> 아래는 Render (https://render.com) 기준 배포 절차입니다. 무료 플랜으로 시작 가능합니다.

### 사전 준비

1. GitHub 저장소가 **public** 상태인지 확인합니다
2. `.env` 파일 내용은 절대 커밋하지 않습니다 (`.gitignore`에 포함됨)
3. OpenAI API 키가 준비되어 있어야 합니다

### Step 1: GitHub에 최신 코드 Push

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning
git add -A
git commit -m "배포 준비 완료"
git push origin main
```

### Step 2: Render 계정 생성 및 로그인

1. https://render.com 에 접속합니다
2. 우측 상단 **Get Started for Free** 클릭
3. **GitHub** 버튼을 눌러 GitHub 계정으로 가입/로그인합니다

### Step 3: 프론트엔드 빌드 (로컬)

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend
npm install
npm run build
```

`frontend/dist/` 폴더가 생성됩니다. 이 빌드 결과물을 백엔드가 자동으로 서빙합니다.

### Step 4: Render에서 Web Service 생성

1. Render 대시보드에서 **New +** → **Web Service** 클릭
2. **Build and deploy from a Git repository** 선택 → **Next**
3. GitHub 저장소 목록에서 **KIT-AI-Learning** 선택 → **Connect**
4. 아래와 같이 설정합니다

| 항목               | 값                                             |
| ------------------ | ---------------------------------------------- |
| **Name**           | `edu-sync-ai` (원하는 이름)                    |
| **Region**         | `Singapore` (한국에서 가장 가까움)             |
| **Branch**         | `main`                                         |
| **Root Directory** | `backend`                                      |
| **Runtime**        | `Python 3`                                     |
| **Build Command**  | `pip install -r requirements.txt`              |
| **Start Command**  | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type**  | `Free` (시작) 또는 `Starter` (안정적)          |

5. **Create Web Service** 클릭

### Step 5: 환경변수 설정

서비스 생성 후 좌측 메뉴에서 **Environment** 클릭 → **Add Environment Variable**:

| Key                   | Value                                             |
| --------------------- | ------------------------------------------------- |
| `OPENAI_API_KEY`      | `sk-...` (본인 OpenAI 키)                         |
| `OPENAI_MODEL`        | `gpt-4o-mini`                                     |
| `LLM_PROVIDER`        | `openai`                                          |
| `EMBEDDING_PROVIDER`  | `openai`                                          |
| `SEED_DATA`           | `1` (데모 시드) 또는 `0` (빈 상태)                |
| `CORS_ALLOW_ORIGINS`  | `https://edu-sync-ai.onrender.com`                |
| `FRONTEND_URL`        | `https://edu-sync-ai.onrender.com`                |
| `KAKAO_REST_API_KEY`  | 카카오 REST API 키                                |
| `KAKAO_CLIENT_SECRET` | 카카오 클라이언트 시크릿                          |
| `KAKAO_REDIRECT_URI`  | `https://edu-sync-ai.onrender.com/oauth/callback` |

> ⚠️ `CORS_ALLOW_ORIGINS`와 `FRONTEND_URL`의 도메인은 Render가 배정한 실제 URL로 교체하세요.

### Step 6: 디스크 연결 (선택 — 데이터 영속화)

무료 플랜은 재배포 시 파일이 초기화됩니다. 데이터를 유지하려면:

1. 서비스 설정 → **Disks** → **Add Disk**
2. **Name**: `edu-sync-data`
3. **Mount Path**: `/data`
4. **Size**: 1 GB

그리고 환경변수에 추가:

| Key        | Value   |
| ---------- | ------- |
| `DATA_DIR` | `/data` |

### Step 7: 배포 확인

1. Render 대시보드에서 **Logs** 탭을 확인합니다
2. `✅ 서버 준비 완료!` 로그가 보이면 성공
3. 브라우저에서 `https://edu-sync-ai.onrender.com/api/health` 접속
4. `{"status":"ok","service":"Edu-Sync AI v3",...}` 확인
5. `https://edu-sync-ai.onrender.com/` 접속 → 웹 프론트엔드 확인

### Step 8: 카카오 오픈빌더 스킬 URL 변경

배포된 Render URL로 스킬 URL을 변경합니다:

- 메인 AI: `https://edu-sync-ai.onrender.com/api/kakao/webhook`
- 조교 예약: `https://edu-sync-ai.onrender.com/api/kakao/webhook/schedule`
- 큐레이션: `https://edu-sync-ai.onrender.com/api/kakao/webhook/curation`

> ngrok 대신 Render URL을 사용하면 24시간 상시 접속 가능합니다.

### 프론트엔드 포함 단일 서버 구조

현재 프로젝트는 **백엔드가 프론트엔드 빌드(`frontend/dist/`)를 직접 서빙**하는 구조입니다.

```
사용자 브라우저
    ↓
https://edu-sync-ai.onrender.com
    ↓
FastAPI (backend/main.py)
    ├── /api/*  →  API 라우터 처리
    └── /*      →  frontend/dist/index.html (SPA)
```

따라서 별도의 프론트엔드 서버가 필요 없습니다. `npm run build` 후 커밋하면 됩니다.

---

## 로컬 프로덕션 빌드 테스트

배포 전 로컬에서 프로덕션 모드를 테스트할 수 있습니다:

```powershell
# 프론트엔드 빌드
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend
npm run build

# 백엔드 실행 (dist/ 자동 감지)
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\backend
uvicorn main:app --host 0.0.0.0 --port 8001
```

`http://localhost:8001` 에서 프론트엔드와 API가 함께 동작합니다.

## 점검 순서

1. `GET /api/health` 확인
2. 관리자에서 날짜 예약 큐레이션 업로드
3. 관리자 달력에서 날짜별 제목과 카테고리 색상 확인
4. 멘토 대시보드에서 오늘 큐레이션 확인
5. 멘토 수강생 관리에서 타임라인과 초대 링크 확인
6. 멘토 자료 업로드와 자료소 확인
7. 조교 스케줄 챗봇과 수동 적용 확인
8. 수강생 웹 챗봇에서 자료 검색 확인
9. 카카오 챗봇과 카카오 조교 예약 흐름 확인

## 핵심 API

- `GET /api/health`
- `POST /api/chat`
- `POST /api/kakao/webhook`
- `POST /api/kakao/webhook/curation`
- `POST /api/kakao/webhook/schedule`
- `GET /api/curation/items`
- `GET /api/curation/today`
- `POST /api/curation/upload`
- `PUT /api/curation/items/{item_id}`
- `DELETE /api/curation/items/{item_id}`
- `GET /api/curation/assets/{item_id}`
- `GET /api/mentor/dashboard`
- `GET /api/mentor/student/{student_id}/timeline`
- `POST /api/mentor/invite`
- `GET /api/mentor/knowledge`
- `POST /api/mentor/knowledge/upload`
- `GET /api/mentor/knowledge/assets/{doc_id}`
- `DELETE /api/mentor/knowledge/{doc_id}`
- `GET /api/ta/slots`
- `POST /api/ta/schedule-assistant`
- `POST /api/ta/slots/bulk`
- `POST /api/ta/book`

---

## 제출 체크리스트

공모전 최종 제출 (2026.04.13 기한):

- [ ] GitHub 저장소 **public** 설정
- [ ] `.env` 파일이 커밋에 포함되지 않음 (API Key 노출 방지)
- [ ] Render 배포 완료 및 라이브 URL 동작 확인
- [ ] AI 리포트 PDF 작성 (양식: `docs/AI_REPORT_GUIDE.md` 참고)
- [ ] 개인정보 수집/이용 동의서 서명 완료
- [ ] 참가 각서 서명 완료
- [ ] 기한 이후 커밋 없음 확인
