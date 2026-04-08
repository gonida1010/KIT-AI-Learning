"""
Edu-Sync AI — FastAPI 백엔드.
멀티 에이전트 기반 KDT 하이브리드 멘토링 시스템.
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.rag import load_or_build_vectorstore, build_curation_vectorstore, get_curation_vectorstore
from services.llm_provider import create_llm_provider, LLMProvider
from db.store import store

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 전역 AI 상태 ─────────────────────────────────────────
vectorstore = None
retriever = None
llm_provider: LLMProvider | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global vectorstore, retriever, llm_provider
    logger.info("🚀 Edu-Sync AI 서버 시작")

    vectorstore = load_or_build_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm_provider = create_llm_provider()

    # 큐레이션 벡터스토어 빌드 (기존 인덱스 없으면 시드 데이터로 빌드)
    if not get_curation_vectorstore() and store.curation_items:
        logger.info("큐레이션 벡터스토어 초기 빌드...")
        build_curation_vectorstore(store.curation_items)

    logger.info("✅ 서버 준비 완료!")
    yield


app = FastAPI(title="Edu-Sync AI", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ──────────────────────────────────────────
from routers import auth, chat, kakao, mentor, ta, knowledge, curation  # noqa: E402

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(kakao.router)
app.include_router(mentor.router)
app.include_router(ta.router)
app.include_router(knowledge.router)
app.include_router(curation.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "Edu-Sync AI v3",
        "vectorstore_loaded": vectorstore is not None,
        "llm_provider": type(llm_provider).__name__ if llm_provider else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5060, reload=True)
