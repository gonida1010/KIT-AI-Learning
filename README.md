# AI 커리큘럼 내비게이터

국비지원 코딩 학원 수강생들이 자신이 배우는 과정의 **학습 맥락**을 파악할 수 있도록 돕는 AI 웹 서비스입니다.

## 프로젝트 구조

```
KIT-AI-Learning/
├── backend/
│   ├── main.py              # FastAPI 서버 + RAG 파이프라인
│   ├── requirements.txt     # Python 패키지
│   ├── .env                 # OpenAI API 키 설정
│   ├── .env.example
│   ├── data/                # 강의 계획서 PDF를 여기에 넣으세요
│   └── vectorstore/         # FAISS 인덱스 (자동 생성)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── DropZone.jsx           # 드래그 앤 드롭 업로드
│   │       ├── Dashboard.jsx          # 분석 결과 대시보드
│   │       ├── ProgressTimeline.jsx   # 진행률 프로그래스 바
│   │       ├── InfoCard.jsx           # 왜 배우나요? / 다음은?
│   │       ├── TermText.jsx           # 전문 용어 툴팁
│   │       └── GlossaryAccordion.jsx  # 용어 사전 아코디언
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
│
└── README.md
```

## 기술 스택

| 영역       | 기술                                                      |
| ---------- | --------------------------------------------------------- |
| Frontend   | React 19, Vite, Tailwind CSS, Lucide React, Framer Motion |
| Backend    | Python, FastAPI, Uvicorn                                  |
| AI/RAG     | LangChain, FAISS, OpenAI API (GPT-4o-mini)                |
| OCR/Vision | OpenAI GPT-4o Vision API                                  |

## 시작하기

### 1. 백엔드

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 패키지 설치
pip install -r requirements.txt

# .env 파일에 OpenAI API 키 설정
# OPENAI_API_KEY=sk-...

# (선택) data/ 폴더에 강의 계획서 PDF 넣기

# 서버 실행 (포트 5060)
python main.py
```

### 2. 프론트엔드

```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행 (포트 3000)
npm run dev
```

### 3. 브라우저에서 접속

`http://localhost:3000` 으로 접속 후, 코드 파일이나 스크린샷을 업로드하세요.

## 주요 기능

1. **파일 분석**: `.py`, `.html`, `.js` 등 코드 파일이나 스크린샷 이미지를 업로드
2. **커리큘럼 위치 파악**: AI가 현재 배우는 내용이 전체 과정 중 어디에 해당하는지 분석
3. **학습 맥락 설명**: "왜 이것을 배우는지", "다음에 뭘 배우는지" 친절하게 안내
4. **용어 툴팁**: 전문 용어에 마우스를 올리면 쉬운 설명이 툴팁으로 표시
5. **용어 사전**: 하단 아코디언에서 전체 용어 목록 확인 가능

## 커리큘럼 PDF 연동

`backend/data/` 폴더에 강의 계획서 PDF를 넣으면, 서버 시작 시 자동으로 임베딩되어 벡터 검색이 가능합니다.

- 서버 실행 중에 PDF를 추가한 경우: `POST /api/rebuild-index` 호출로 인덱스를 재구축할 수 있습니다.
- PDF가 없어도 일반적인 프로그래밍 커리큘럼 기준으로 분석이 가능합니다.
