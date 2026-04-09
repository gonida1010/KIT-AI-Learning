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
KAKAO_REDIRECT_URI=http://localhost:3000
FRONTEND_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000
```

### 4. 백엔드 실행

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 5060 --reload
```

### 5. 프론트엔드 실행

```powershell
cd c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend
npm install
npm run dev
```

### 6. 확인 주소

- 프론트엔드: `http://localhost:3000`
- 백엔드 헬스체크: `http://localhost:5060/api/health`

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

### 오픈빌더 스킬 URL 예시

- 메인 AI: `https://your-domain.com/api/kakao/webhook`
- 큐레이션 조회: `https://your-domain.com/api/kakao/webhook/curation`
- 조교 예약: `https://your-domain.com/api/kakao/webhook/schedule`

## 운영 전 체크 포인트

- 토큰 전달은 query string 대신 `Authorization` 헤더 또는 HttpOnly cookie로 변경 권장
- 현재 JSON 저장소는 시연용이며 운영 전 PostgreSQL 권장
- 세션 및 임시 상태는 Redis 도입 권장
- 첨부 파일 MIME 검사, 파일 크기 제한, 악성 파일 검사 추가 권장
- 외부 링크 허용 도메인 정책과 redirect 검증 권장

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

## 14. 현재 결론

- AI 사용 중: 맞음
- 멀티 에이전트 구조: 맞음
- 벡터 저장소 연결: 맞음
- 관리자/멘토/조교 대시보드 분리: 맞음
- 드래그 업로드: 맞음
- 카카오 연동 가능: 맞음
- 카카오 쪽 수동 설정 필요: 맞음
- 로컬 구동 가능: 맞음
- 운영 배포 전 DB/인증 보강 필요: 맞음
