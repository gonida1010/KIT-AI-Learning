"""
큐레이션 관리 API — 학원에서 업로드한 일일 정보 콘텐츠.
월(채용정보) · 화(IT뉴스) · 수(AI타임스) · 목(자격증/공모전) · 금(개발트렌드)
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from db.store import store
from services.rag import DATA_DIR, add_curation_to_vectorstore, build_curation_vectorstore

router = APIRouter(prefix="/api/curation", tags=["curation"])

SCHEDULE_MAP = {0: "채용정보", 1: "IT뉴스", 2: "AI타임스", 3: "자격증·공모전", 4: "개발트렌드"}


@router.get("/items")
async def list_curations(category: str | None = None, date: str | None = None):
    """큐레이션 목록 (필터 가능)."""
    return store.get_curations(category=category, date=date)


@router.get("/schedule")
async def get_schedule():
    """요일별 큐레이션 카테고리 스케줄."""
    return {"schedule": SCHEDULE_MAP}


@router.get("/today")
async def today_curation():
    """오늘 날짜의 큐레이션 항목."""
    today = datetime.now().strftime("%Y-%m-%d")
    items = store.get_curations(date=today)
    weekday = datetime.now().weekday()
    category = SCHEDULE_MAP.get(weekday, None)
    return {"date": today, "category": category, "items": items}


@router.post("/upload")
async def upload_curation(
    file: UploadFile = File(...),
    category: str = Form("기타"),
    title: str = Form(""),
    summary: str = Form(""),
    date: str = Form(""),
):
    """학원에서 PDF 큐레이션 콘텐츠 업로드."""
    if not file.filename:
        raise HTTPException(400, "파일명 없음")

    DATA_DIR.mkdir(exist_ok=True)
    file_path = DATA_DIR / file.filename
    content_bytes = await file.read()
    file_path.write_bytes(content_bytes)

    # PDF이면 텍스트 추출
    content_text = ""
    if file.filename.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content_text += text + "\n"

    target_date = date or datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.strptime(target_date, "%Y-%m-%d").weekday()

    item = {
        "id": uuid.uuid4().hex[:12],
        "category": category,
        "title": title or file.filename,
        "summary": summary or content_text[:200],
        "content": content_text or "(PDF 외 파일 — 내용 미추출)",
        "date": target_date,
        "weekday": weekday,
        "source_filename": file.filename,
        "tags": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    store.add_curation(item)

    # 벡터스토어에도 추가 인덱싱
    add_curation_to_vectorstore(item)

    return {"status": "ok", "item": item}


@router.delete("/items/{item_id}")
async def delete_curation(item_id: str):
    for i, item in enumerate(store.curation_items):
        if item["id"] == item_id:
            store.curation_items.pop(i)
            store._save()
            # 벡터스토어 재빌드 (삭제 후 동기화)
            build_curation_vectorstore(store.curation_items)
            return {"status": "ok"}
    raise HTTPException(404, "항목 없음")
