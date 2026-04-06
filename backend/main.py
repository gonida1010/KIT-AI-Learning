"""
AI 커리큘럼 내비게이터 — FastAPI 백엔드
"""

import os
import re
import json
import base64
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document, HumanMessage

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
CODE_EXTENSIONS = {".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".json", ".sql", ".ipynb"}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
vectorstore = None
retriever = None
llm = None
vision_llm = None

# ---------------------------------------------------------------------------
# RAG Pipeline – 커리큘럼 PDF 임베딩
# ---------------------------------------------------------------------------

def load_pdf_documents(data_dir: Path) -> list[Document]:
    """data 폴더에서 PDF 파일 로드."""
    from pypdf import PdfReader

    docs: list[Document] = []
    for pdf_path in data_dir.glob("*.pdf"):
        logger.info(f"PDF 로드 중: {pdf_path.name}")
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        if full_text.strip():
            docs.append(Document(page_content=full_text, metadata={"source": pdf_path.name}))
    return docs


def build_vectorstore(documents: list[Document]) -> FAISS:
    """문서를 청크로 나누고 FAISS 벡터 저장소를 빌드."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"총 {len(chunks)}개의 청크를 임베딩합니다.")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(VECTORSTORE_DIR))
    return vs


def load_or_build_vectorstore() -> FAISS | None:
    """기존 벡터스토어가 있으면 로드, 없으면 PDF에서 빌드."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    if (VECTORSTORE_DIR / "index.faiss").exists():
        logger.info("기존 FAISS 벡터스토어를 로드합니다.")
        return FAISS.load_local(
            str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
        )

    DATA_DIR.mkdir(exist_ok=True)
    pdf_docs = load_pdf_documents(DATA_DIR)
    if not pdf_docs:
        logger.warning("data/ 폴더에 PDF가 없습니다. 벡터스토어를 초기화하지 않습니다.")
        return None

    return build_vectorstore(pdf_docs)

# ---------------------------------------------------------------------------
# Vision / OCR – 이미지에서 코드·텍스트 추출
# ---------------------------------------------------------------------------

async def extract_text_from_image(image_bytes: bytes, mime_type: str) -> str:
    """OpenAI GPT-4o Vision을 이용해 이미지에서 텍스트/코드를 추출."""
    b64 = base64.b64encode(image_bytes).decode()
    response = vision_llm.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": "이 이미지에 포함된 모든 텍스트와 코드를 추출해 주세요. 코드가 있다면 프로그래밍 언어도 알려 주세요. 텍스트만 출력하세요."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                ]
            )
        ]
    )
    return response.content

# ---------------------------------------------------------------------------
# LLM 분석 체인
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
당신은 국비지원 코딩 학원의 AI 학습 내비게이터입니다.
학습자가 올린 코드나 텍스트를 분석하여, 커리큘럼 내에서의 위치와 학습 맥락을 친절하게 설명합니다.

아래는 커리큘럼 문서에서 검색된 관련 정보입니다:
---
{context}
---

분석할 코드/텍스트:
```
{code}
```

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
설명 텍스트 내의 전문 용어는 반드시 <term>용어</term> 형태로 태깅하세요.

{{
  "location": "N개월 차 - 해당 단원/주제명",
  "progress_percentage": 0~100 사이 숫자,
  "why_learn": "이 코드가 무엇인지, 왜 배우는지에 대한 설명 (전문 용어를 <term> 태그로 감쌈)",
  "whats_next": "이 이후에 배울 내용에 대한 설명 (전문 용어를 <term> 태그로 감쌈)",
  "glossary": {{
    "용어1": "쉬운 설명",
    "용어2": "쉬운 설명"
  }}
}}
"""


def extract_json(text: str) -> dict:
    """LLM 응답에서 JSON만 추출한다."""
    # Try to find a JSON block in markdown code fences first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    # Try to locate outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    raise ValueError("LLM 응답에서 JSON을 찾을 수 없습니다.")


async def analyze_code(code_text: str) -> dict:
    """코드 분석 → 벡터 검색 → LLM 생성."""
    context = ""
    if retriever:
        docs = retriever.invoke(code_text[:1000])
        context = "\n\n".join(d.page_content for d in docs)

    prompt = SYSTEM_PROMPT.format(context=context or "(커리큘럼 문서가 아직 업로드되지 않았습니다. 일반적인 프로그래밍 커리큘럼을 기준으로 답변하세요.)", code=code_text[:3000])

    response = llm.invoke([HumanMessage(content=prompt)])
    return extract_json(response.content)

# ---------------------------------------------------------------------------
# FastAPI Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vectorstore, retriever, llm, vision_llm
    logger.info("서버 시작 — 벡터스토어 초기화 중...")

    vectorstore = load_or_build_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    vision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_tokens=2048)

    logger.info("서버 준비 완료!")
    yield

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="AI 커리큘럼 내비게이터", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "vectorstore_loaded": vectorstore is not None}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """파일을 받아 분석 결과 JSON을 반환한다."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = Path(file.filename).suffix.lower()
    content_bytes = await file.read()

    if not content_bytes:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    # 이미지 → Vision 추출 → 분석
    if ext in IMAGE_EXTENSIONS:
        mime = file.content_type or "image/png"
        code_text = await extract_text_from_image(content_bytes, mime)
    elif ext in CODE_EXTENSIONS or ext == ".txt":
        code_text = content_bytes.decode("utf-8", errors="replace")
    else:
        # 기타 텍스트 시도
        try:
            code_text = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    try:
        result = await analyze_code(code_text)
    except Exception as e:
        logger.exception("분석 실패")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {e}")

    return result


@app.post("/api/rebuild-index")
async def rebuild_index():
    """data/ 폴더의 PDF를 다시 임베딩한다."""
    global vectorstore, retriever
    pdf_docs = load_pdf_documents(DATA_DIR)
    if not pdf_docs:
        raise HTTPException(status_code=400, detail="data/ 폴더에 PDF 파일이 없습니다.")
    vectorstore = build_vectorstore(pdf_docs)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return {"status": "ok", "message": "인덱스를 재구축했습니다."}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5060, reload=True)
