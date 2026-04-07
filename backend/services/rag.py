"""
RAG 파이프라인 — 벡터스토어 구축 및 검색.
"""

import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


def load_pdf_documents(data_dir: Path | None = None) -> list[Document]:
    """data 폴더에서 PDF 파일 로드."""
    from pypdf import PdfReader

    folder = data_dir or DATA_DIR
    docs: list[Document] = []
    for pdf_path in folder.glob("*.pdf"):
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
            str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True,
        )

    DATA_DIR.mkdir(exist_ok=True)
    pdf_docs = load_pdf_documents()
    if not pdf_docs:
        logger.warning("data/ 폴더에 PDF가 없습니다. 벡터스토어 미초기화.")
        return None

    return build_vectorstore(pdf_docs)


def add_documents_to_vectorstore(vs: FAISS, documents: list[Document]) -> FAISS:
    """기존 벡터스토어에 문서를 추가."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100, separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(documents)
    vs.add_documents(chunks)
    vs.save_local(str(VECTORSTORE_DIR))
    return vs
