"""
Edu-Sync AI — FastAPI 백엔드 메인 엔트리포인트
차세대 KDT 하이브리드 관리 플랫폼
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import ChatOpenAI

from services.rag import load_or_build_vectorstore

load_dotenv()

# ── 로깅 ─────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 전역 AI 상태 ─────────────────────────────────────────
vectorstore = None
retriever = None
llm = None
vision_llm = None


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global vectorstore, retriever, llm, vision_llm
    logger.info("🚀 Edu-Sync AI 서버 시작 — 벡터스토어 초기화 중...")

    vectorstore = load_or_build_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    vision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_tokens=2048)

    logger.info("✅ 서버 준비 완료!")
    yield


# ── FastAPI App ──────────────────────────────────────────
app = FastAPI(title="Edu-Sync AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ──────────────────────────────────────────
from routers import auth, chat, kakao, mentor, ta, analyze, knowledge  # noqa: E402

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(kakao.router)
app.include_router(mentor.router)
app.include_router(ta.router)
app.include_router(analyze.router)
app.include_router(knowledge.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "Edu-Sync AI",
        "vectorstore_loaded": vectorstore is not None,
    }


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5060, reload=True)
