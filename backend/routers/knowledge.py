"""지식 베이스 관리 API — 문서 업로드, 목록, 삭제, 인덱스 재구축."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from db.store import store
from services.rag import load_pdf_documents, build_vectorstore, add_documents_to_vectorstore, DATA_DIR

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), doc_type: str = Form("기타")):
    from main import vectorstore, retriever
    import main

    if not file.filename:
        raise HTTPException(400, "파일명 없음")

    DATA_DIR.mkdir(exist_ok=True)
    file_path = DATA_DIR / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    chunk_count = 0
    if file.filename.lower().endswith(".pdf"):
        from langchain.schema import Document
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        if full_text.strip():
            doc = Document(page_content=full_text, metadata={"source": file.filename})
            if main.vectorstore:
                main.vectorstore = add_documents_to_vectorstore(main.vectorstore, [doc])
            else:
                main.vectorstore = build_vectorstore([doc])
            main.retriever = main.vectorstore.as_retriever(search_kwargs={"k": 4})
            chunk_count = len(full_text) // 600 + 1

    rec = {
        "id": uuid.uuid4().hex[:12],
        "filename": file.filename,
        "doc_type": doc_type,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "chunk_count": chunk_count,
    }
    store.add_knowledge_doc(rec)
    return {"status": "ok", "document": rec}


@router.get("/documents")
async def list_documents():
    return store.get_knowledge_docs()


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    if store.remove_knowledge_doc(doc_id):
        return {"status": "ok"}
    raise HTTPException(404, "문서 없음")


@router.post("/rebuild")
async def rebuild_index():
    import main

    pdf_docs = load_pdf_documents()
    if not pdf_docs:
        raise HTTPException(400, "data/ 에 PDF 없음")
    main.vectorstore = build_vectorstore(pdf_docs)
    main.retriever = main.vectorstore.as_retriever(search_kwargs={"k": 4})
    return {"status": "ok", "message": "인덱스 재구축 완료"}
