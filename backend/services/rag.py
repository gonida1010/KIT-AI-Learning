"""
RAG 파이프라인 — FAISS 벡터스토어 구축 및 검색.
임베딩 프로바이더도 On-Premise 전환 가능 (환경변수 EMBEDDING_PROVIDER).
"""

import os
import logging
from pathlib import Path

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


def _get_embeddings():
    """환경변수에 따라 임베딩 모델 선택 (OpenAI 기본, On-Premise 전환 가능)."""
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if provider == "onpremise":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            base_url=os.getenv("EMBEDDING_BASE_URL", "http://localhost:8000/v1"),
            model=os.getenv("EMBEDDING_MODEL", "default"),
            api_key=os.getenv("EMBEDDING_API_KEY", "not-needed"),
        )
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model="text-embedding-3-small")


def load_pdf_documents(data_dir: Path | None = None) -> list[Document]:
    """data 폴더에서 PDF 파일 로드."""
    from pypdf import PdfReader

    folder = data_dir or DATA_DIR
    docs: list[Document] = []
    for pdf_path in folder.glob("*.pdf"):
        logger.info(f"PDF 로드: {pdf_path.name}")
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        if full_text.strip():
            docs.append(
                Document(page_content=full_text, metadata={"source": pdf_path.name})
            )
    return docs


def build_vectorstore(documents: list[Document]):
    from langchain_community.vectorstores import FAISS

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"총 {len(chunks)}개 청크 임베딩")
    embeddings = _get_embeddings()
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(VECTORSTORE_DIR))
    return vs


def load_or_build_vectorstore():
    from langchain_community.vectorstores import FAISS

    embeddings = _get_embeddings()
    if (VECTORSTORE_DIR / "index.faiss").exists():
        logger.info("기존 FAISS 벡터스토어 로드")
        return FAISS.load_local(
            str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
        )
    DATA_DIR.mkdir(exist_ok=True)
    pdf_docs = load_pdf_documents()
    if not pdf_docs:
        logger.warning("data/ 에 PDF 없음 — 벡터스토어 미초기화")
        return None
    return build_vectorstore(pdf_docs)


def add_documents_to_vectorstore(vs, documents: list[Document]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    vs.add_documents(chunks)
    vs.save_local(str(VECTORSTORE_DIR))
    return vs


# ━━━━━━━━━━━━━━━━━━ 큐레이션 벡터스토어 ━━━━━━━━━━━━━━━━━━
CURATION_VS_DIR = BASE_DIR / "vectorstore_curation"
_curation_vs = None
MENTOR_VS_DIR = BASE_DIR / "vectorstore_mentor"
_mentor_vs_map: dict[str, object] = {}


def build_curation_vectorstore(curation_items: list[dict]):
    """큐레이션 아이템 리스트를 FAISS 벡터스토어로 빌드."""
    from langchain_community.vectorstores import FAISS

    global _curation_vs
    if not curation_items:
        logger.warning("큐레이션 아이템 없음 — 벡터스토어 미생성")
        return None

    docs = []
    for item in curation_items:
        text = (
            f"[{item['category']}] {item['title']}\n"
            f"날짜: {item['date']}\n"
            f"요약: {item.get('summary', '')}\n"
            f"내용: {item.get('content', '')}"
        )
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "curation_id": item["id"],
                    "category": item["category"],
                    "date": item["date"],
                    "title": item["title"],
                },
            )
        )

    embeddings = _get_embeddings()
    vs = FAISS.from_documents(docs, embeddings)
    CURATION_VS_DIR.mkdir(exist_ok=True)
    vs.save_local(str(CURATION_VS_DIR))
    _curation_vs = vs
    logger.info(f"큐레이션 벡터스토어 빌드 완료: {len(docs)}건")
    return vs


def get_curation_vectorstore():
    """큐레이션 벡터스토어 로드 (없으면 None)."""
    from langchain_community.vectorstores import FAISS

    global _curation_vs
    if _curation_vs is not None:
        return _curation_vs

    if (CURATION_VS_DIR / "index.faiss").exists():
        embeddings = _get_embeddings()
        _curation_vs = FAISS.load_local(
            str(CURATION_VS_DIR), embeddings, allow_dangerous_deserialization=True
        )
        return _curation_vs
    return None


def add_curation_to_vectorstore(item: dict):
    """단일 큐레이션 아이템을 기존 벡터스토어에 추가."""
    global _curation_vs
    vs = get_curation_vectorstore()
    if vs is None:
        vs = build_curation_vectorstore([item])
        return vs

    text = (
        f"[{item['category']}] {item['title']}\n"
        f"날짜: {item['date']}\n"
        f"요약: {item.get('summary', '')}\n"
        f"내용: {item.get('content', '')}"
    )
    doc = Document(
        page_content=text,
        metadata={
            "curation_id": item["id"],
            "category": item["category"],
            "date": item["date"],
            "title": item["title"],
        },
    )
    vs.add_documents([doc])
    vs.save_local(str(CURATION_VS_DIR))
    _curation_vs = vs
    return vs


def search_curation_vectorstore(query: str, k: int = 6) -> list[dict]:
    """큐레이션 벡터스토어에서 유사도 검색."""
    vs = get_curation_vectorstore()
    if vs is None:
        return []
    results = vs.similarity_search_with_score(query, k=k)
    items = []
    for doc, score in results:
        items.append({
            "content": doc.page_content,
            "score": float(score),
            **doc.metadata,
        })
    return items


def _mentor_vectorstore_dir(mentor_id: str) -> Path:
    return MENTOR_VS_DIR / mentor_id


def get_mentor_vectorstore(mentor_id: str):
    from langchain_community.vectorstores import FAISS

    if mentor_id in _mentor_vs_map:
        return _mentor_vs_map[mentor_id]

    mentor_dir = _mentor_vectorstore_dir(mentor_id)
    if (mentor_dir / "index.faiss").exists():
        embeddings = _get_embeddings()
        _mentor_vs_map[mentor_id] = FAISS.load_local(
            str(mentor_dir), embeddings, allow_dangerous_deserialization=True
        )
        return _mentor_vs_map[mentor_id]
    return None


def build_mentor_vectorstore(mentor_id: str, documents: list[Document]):
    from langchain_community.vectorstores import FAISS

    mentor_dir = _mentor_vectorstore_dir(mentor_id)
    mentor_dir.mkdir(parents=True, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    embeddings = _get_embeddings()
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(mentor_dir))
    _mentor_vs_map[mentor_id] = vs
    return vs


def add_mentor_document_to_vectorstore(mentor_id: str, documents: list[Document]):
    vs = get_mentor_vectorstore(mentor_id)
    if vs is None:
        return build_mentor_vectorstore(mentor_id, documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    vs.add_documents(chunks)
    vs.save_local(str(_mentor_vectorstore_dir(mentor_id)))
    _mentor_vs_map[mentor_id] = vs
    return vs


def rebuild_mentor_vectorstore(mentor_id: str, documents: list[Document]):
    if not documents:
        return None
    return build_mentor_vectorstore(mentor_id, documents)


def search_mentor_vectorstore(mentor_id: str, query: str, k: int = 3) -> list[dict]:
    vs = get_mentor_vectorstore(mentor_id)
    if vs is None:
        return []

    results = vs.similarity_search_with_score(query, k=k)
    items = []
    for doc, score in results:
        items.append({
            "content": doc.page_content,
            "score": float(score),
            **doc.metadata,
        })
    return items
