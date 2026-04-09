# Edu-Sync AI

KDT 운영용 멀티 에이전트 학습 지원 시스템입니다.
현재 구현 기준으로 관리자, 멘토, 조교, 수강생 화면과 챗봇 흐름이 분리되어 있으며, 자료 업로드는 AI 요약 후 벡터 저장소에 연결됩니다.

---

## 1. 실제 제출용 전체 개발 파이프라인

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

### 3. 백엔드 환경변수 파일 생성

파일 경로:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\.env`

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

### 6. 로컬 확인 경로

- 프론트: `http://localhost:3000`
- 백엔드 헬스체크: `http://localhost:5060/api/health`

### 7. 자동 초기화되는 항목

서버 시작 시 아래가 자동으로 준비됩니다.

- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\db\app_data.json` 시드 데이터 생성
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore` 공통 문서 벡터 저장소
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore_curation` 큐레이션 벡터 저장소
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore_mentor\<mentor_id>` 멘토별 벡터 저장소

---

## 2. 역할별 실제 화면 구조

### 관리자

파일:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend\src\pages\AdminDashboard.jsx`

기능:

- 상단 카테고리 탭 바로 노출
- 달력 클릭 기반 큐레이션 등록
- 파일 드래그 앤 드롭 업로드
- 외부 링크 등록
- 달력에서 비어 있는 날짜 / 등록된 날짜 색상 구분
- 달력에서 날짜별 등록 현황 확인
- 날짜 클릭 후 해당 날짜 자료 확인
- 날짜/카테고리 수정 가능
- 삭제 가능
- 첨부 열기 가능
- 우측 등록 내용 패널 높이 고정으로 반응형 레이아웃 흔들림 최소화

### 멘토

파일:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend\src\pages\MentorDashboard.jsx`

기능:

- 최근 24시간 질문 기록
- 학생에게 송부된 자료 기록
- 오늘 큐레이션 표시
- 내 최신 자료 5개 표시
- 대시보드에서 바로 자료 드래그 업로드

멘토 자료소 파일:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend\src\pages\KnowledgeBase.jsx`

기능:

- 멘토 전용 자료 업로드
- 파일 드래그 앤 드롭 업로드
- 외부 링크 등록
- 최신 자료 / 오래된 자료 분리
- 첨부 열기 / 삭제

### 조교

파일:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend\src\pages\TADashboard.jsx`

기능:

- 다음달 포함 원하는 기간의 스케줄 일괄 등록
- 기본 가능시간 09:00-22:00, 1시간 단위 일괄 초기 설정
- 휴무 / 불가 시간 전용 설정
- 날짜 클릭 시 그날의 예약 / 휴무 / 가능 시간 확인
- 예약자 이름 확인
- 공부 내용 확인
- LLM 브리핑 확인
- 향후 조교 직접 선택 또는 AI 기반 최적 조교 배정으로 확장 가능

### 수강생

파일:
`c:\Pyg\Projects\KIT\KIT-AI-Learning\frontend\src\pages\StudentChat.jsx`

기능:

- 웹 챗봇 대화
- 큐레이션 송부
- 멘토 자료 송부
- 조교 예약 유도
- 멘토 연결 유도

---

## 3. 실제 백엔드 연결 경로

- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\main.py`
  - FastAPI 시작
  - LLM / 벡터 저장소 초기화
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\routers\chat.py`
  - 웹 챗봇
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\routers\kakao.py`
  - 카카오 챗봇 웹훅
  - 카카오 조교 예약 클릭 흐름
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\routers\curation.py`
  - 공통 큐레이션 등록 / 수정 / 삭제 / 첨부 열기
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\routers\mentor.py`
  - 멘토 자료 등록 / 조회 / 삭제 / 첨부 열기
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\routers\ta.py`
  - 조교 시간 등록 / 휴무 등록 / 예약 처리
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\services\agent_router.py`
  - 멀티 에이전트 라우터
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\services\agent_a.py`
  - 취업 / 행정 / 큐레이션 / 멘토 자료 응답
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\services\agent_b.py`
  - 학습 / 조교 / 예약 응답
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\services\rag.py`
  - 공통 / 큐레이션 / 멘토 벡터 저장소
- `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\services\llm_provider.py`
  - OpenAI / 온프레미스 LLM 연결

---

## 4. AI 사용 여부 점검

현재 코드 기준으로 AI는 실제로 사용됩니다.

### LLM 사용 위치

- 질문 의도 분기: `backend/services/agent_router.py`
- 행정/취업 응답 생성: `backend/services/agent_a.py`
- 학습/조교 응답 생성: `backend/services/agent_b.py`
- 관리자 큐레이션 업로드 요약: `backend/routers/curation.py`
- 멘토 자료 업로드 요약: `backend/routers/mentor.py`
- 조교 브리핑 생성: `backend/services/agent_b.py`

### 벡터 DB 사용 위치

- 공통 자료: `backend/vectorstore`
- 공통 큐레이션: `backend/vectorstore_curation`
- 멘토 전용 자료: `backend/vectorstore_mentor\<mentor_id>`

### 업로드 자료와 챗봇 연결 여부

연결되어 있습니다.

- 멘토가 자료 업로드
- AI가 제목/요약 생성
- 멘토 벡터 저장소에 적재
- 학생 질문 시 `agent_a.py` 가 유사도 검색
- 관련 자료 최대 3개를 챗봇 응답에 포함

관리자 큐레이션도 같은 방식으로 연결됩니다.

---

## 5. 멀티 에이전트 구조 점검

현재 구조는 멀티 에이전트 맞습니다.

- Router Agent: 질문 분류
- Agent A: 취업, 행정, 큐레이션, 멘토 자료
- Agent B: 학습, 조교, 예약
- Human handoff: 멘토 연결

즉 단일 프롬프트 챗봇이 아니라 질문에 따라 응답 책임이 나뉘는 구조입니다.

---

## 6. 관리자 큐레이션 실제 동작 방식

1. 관리자가 카테고리 선택
2. 노출 날짜 선택
3. 파일 드래그 업로드 또는 링크 등록
4. 서버가 파일 내용을 읽음
5. AI가 제목과 요약 생성
6. 큐레이션 메타데이터 저장
7. 큐레이션 벡터 저장소에 적재
8. 해당 날짜가 되면 멘토 대시보드의 `오늘 큐레이션` 에 표시
9. 챗봇도 같은 날짜 자료를 검색 가능

즉 관리자가 미리 다음 주, 다음 달 자료를 예약해 둘 수 있습니다.

---

## 7. 멘토 자료 실제 동작 방식

1. 멘토가 대시보드 또는 지식베이스에서 파일 업로드
2. 서버가 파일 내용을 읽음
3. AI가 제목과 요약 생성
4. 멘토 전용 벡터 저장소에 적재
5. 학생 질문 시 유사도 검색
6. 관련 멘토 자료를 학생 챗봇 응답에 포함

저장 위치:

- 메타데이터: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\db\app_data.json`
- 첨부 원본: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\data\mentor_assets\<mentor_id>`
- 벡터 저장소: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore_mentor\<mentor_id>`

---

## 8. 조교 예약 및 카카오 흐름

### 조교 스케줄

조교는 다음이 가능합니다.

- 원하는 기간 선택
- 여러 요일 선택
- 시간대 선택
- 예약 가능 시간 등록
- 휴무 / 불가 시간 등록

### 카카오 예약 흐름

현재 백엔드 기준 흐름:

1. 학생이 카카오 메뉴에서 조교 보충 수업 클릭
2. `/api/kakao/webhook/schedule` 에서 예약 가능한 시간 Quick Reply 노출
3. 학생이 시간 클릭
4. 학생이 어려운 내용을 한 줄로 입력
5. 서버가 LLM 브리핑 생성
6. 조교 대시보드에 아래 정보 저장
   - 시간
   - 예약자
   - 공부 내용
   - LLM 브리핑

즉 조교 대시보드에서 학생 예약 내용을 바로 확인할 수 있습니다.

---

## 9. 보안 점검 결과

### 현재 반영된 항목

- CORS를 `*` 에서 환경변수 기반 허용 목록으로 변경
- 환경변수: `CORS_ALLOW_ORIGINS`

### 운영 배포 전에 반드시 바꿔야 하는 항목

1. 토큰 전달 방식

- 현재 일부 API는 query string token 사용
- 운영 전 `Authorization` 헤더 또는 HttpOnly cookie 권장

2. DB 저장소

- 현재는 JSON 파일 기반
- 운영 전 PostgreSQL 권장

3. 세션/임시 상태

- 운영 전 Redis 권장

4. 첨부 검증

- 운영 전 MIME 검사, 파일 크기 제한, 악성 파일 검사 추가 권장

5. 링크 검증

- 운영 전 허용 도메인 정책과 redirect 검증 권장

---

## 10. DB를 실제로 만들어야 하는지

### 로컬 시연

지금은 없어도 됩니다.

현재 로컬 저장 구조:

- 일반 데이터: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\db\app_data.json`
- 공통 벡터 저장소: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore`
- 큐레이션 벡터 저장소: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore_curation`
- 멘토 벡터 저장소: `c:\Pyg\Projects\KIT\KIT-AI-Learning\backend\vectorstore_mentor`

### 실제 운영 제출

운영형 제출이면 만드는 게 맞습니다.

권장 구조:

- PostgreSQL
- Redis
- FAISS 영속 볼륨 또는 외부 Vector DB

즉 답은 아래와 같습니다.

- 로컬 실행: DB 없이 가능
- 실제 서비스 운영: PostgreSQL + Redis 권장

---

## 11. 카카오톡 연동 시 직접 해야 하는 것

코드만으로 자동 완료되지 않습니다. 아래는 직접 해야 합니다.

1. Kakao Developers 앱 생성
2. REST API 키 발급
3. Redirect URI 등록
4. 카카오톡 채널 생성
5. 카카오 i 오픈빌더 봇 생성
6. 채널 연결
7. 운영 HTTPS 도메인 준비
8. 오픈빌더 스킬 URL 등록
9. 상시 메뉴 직접 구성
10. 실제 채널 배포 후 테스트

### 오픈빌더에 넣을 URL

- 메인 AI: `https://your-domain.com/api/kakao/webhook`
- 큐레이션 조회: `https://your-domain.com/api/kakao/webhook/curation`
- 조교 예약: `https://your-domain.com/api/kakao/webhook/schedule`

### 상시 메뉴 예시

- 취업·채용 정보, IT 뉴스
- 수강생 기초 자료
- 조교 보충 수업
- 자격증·공모전 정보
- 필요한 정보 채팅(AI)
- 멘토 연결

---

## 12. 실제 점검 순서

1. `http://localhost:5060/api/health` 확인
2. 관리자 로그인 후 날짜 예약 큐레이션 업로드
3. 관리자 달력에서 날짜별 자료 확인
4. 멘토 대시보드에서 오늘 큐레이션 노출 확인
5. 멘토 대시보드에서 바로 자료 업로드 확인
6. 멘토 지식베이스에서 드래그 업로드 확인
7. 수강생 챗봇에서 질문 후 관련 자료 송부 확인
8. 카카오 챗봇에서 같은 질문 확인
9. 카카오 조교 예약 Quick Reply 확인
10. 조교 대시보드에서 예약자/공부내용/브리핑 확인

---

## 13. 현재 핵심 API

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
- `GET /api/mentor/knowledge`
- `POST /api/mentor/knowledge/upload`
- `GET /api/mentor/knowledge/assets/{doc_id}`
- `DELETE /api/mentor/knowledge/{doc_id}`
- `GET /api/ta/slots`
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
