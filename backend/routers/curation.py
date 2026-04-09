"""큐레이션 관리 API — 공통 큐레이션 업로드, AI 정리, 첨부 열람."""

import mimetypes
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from db.store import store
from services.rag import DATA_DIR, add_curation_to_vectorstore, build_curation_vectorstore

router = APIRouter(prefix="/api/curation", tags=["curation"])
CURATION_ASSET_DIR = DATA_DIR / "curation_assets"

SCHEDULE_MAP = {0: "채용정보", 1: "IT뉴스", 2: "AI타임스", 3: "자격증·공모전", 4: "개발트렌드"}


class UpdateCurationRequest(BaseModel):
    category: str
    date: str


def _find_curation_by_date(target_date: str, exclude_item_id: str | None = None) -> dict | None:
    for item in store.curation_items:
        if item.get("date") != target_date:
            continue
        if exclude_item_id and item.get("id") == exclude_item_id:
            continue
        return item
    return None


@router.get("/items")
async def list_curations(category: str | None = None, date: str | None = None):
    """큐레이션 목록 (필터 가능)."""
    items = store.get_curations(category=category, date=date)
    return [_serialize_curation(item) for item in items]


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
    return {
        "date": today,
        "category": category,
        "items": [_serialize_curation(item) for item in items],
    }


def _fallback_digest(raw_text: str, fallback_name: str) -> tuple[str, str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0][:60] if lines else Path(fallback_name).stem
    summary = " ".join(lines[1:4])[:180] if len(lines) > 1 else f"{title} 관련 자료"
    return title or Path(fallback_name).stem, summary or f"{fallback_name} 관련 자료"


async def _build_ai_digest(raw_text: str, fallback_name: str) -> tuple[str, str]:
    from main import llm_provider

    cleaned = (raw_text or "").strip()
    if not cleaned:
        return _fallback_digest("", fallback_name)

    prompt = """
당신은 학원 공지 자료 정리 비서입니다.
업로드된 원문을 읽고 학원 수강생에게 바로 보여줄 수 있게 정리하세요.

반드시 아래 JSON 형식으로만 답변하세요:
{
  "title": "짧고 명확한 제목",
  "summary": "한두 문장 요약"
}
"""

    if not llm_provider:
        return _fallback_digest(cleaned, fallback_name)

    try:
        result = await llm_provider.chat_json(prompt, cleaned[:4000])
        title = (result.get("title") or "").strip()
        summary = (result.get("summary") or "").strip()
        if title and summary:
            return title[:80], summary[:220]
    except Exception:
        pass

    return _fallback_digest(cleaned, fallback_name)


def _serialize_curation(item: dict) -> dict:
    data = dict(item)
    attachment_kind = data.get("attachment_kind") or ("file" if data.get("source_filename") else None)
    data["attachment_kind"] = attachment_kind
    if attachment_kind == "link":
        data["attachment_url"] = data.get("source_url")
    elif data.get("id"):
        data["attachment_url"] = f"/api/curation/assets/{data['id']}"
    return data


@router.post("/upload")
async def upload_curation(
    file: UploadFile | None = File(default=None),
    category: str = Form("기타"),
    date: str = Form(""),
    source_link: str = Form(""),
):
    """관리자가 공통 큐레이션 콘텐츠 업로드. 제목/요약은 AI가 정리한다."""
    if file is None and not source_link.strip():
        raise HTTPException(400, "파일 또는 링크가 필요합니다.")

    target_date = date or datetime.now().strftime("%Y-%m-%d")
    if _find_curation_by_date(target_date):
        raise HTTPException(400, "하루에는 큐레이션 자료를 1개만 등록할 수 있습니다. 기존 자료를 수정하거나 삭제해 주세요.")

    CURATION_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    attachment_kind = "link" if source_link.strip() and file is None else "file"
    file_name = ""
    content_text = ""
    stored_path = None

    if file is not None:
        if not file.filename:
            raise HTTPException(400, "파일명 없음")
        file_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
        stored_path = CURATION_ASSET_DIR / file_name
        content_bytes = await file.read()
        stored_path.write_bytes(content_bytes)

        suffix = stored_path.suffix.lower()
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(stored_path))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content_text += text + "\n"
        else:
            content_text = f"첨부 파일명: {Path(file.filename).stem}"
            if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                attachment_kind = "image"
    else:
        content_text = f"외부 링크 자료: {source_link.strip()}"

    weekday = datetime.strptime(target_date, "%Y-%m-%d").weekday()
    ai_title, ai_summary = await _build_ai_digest(content_text, file_name or source_link)

    item = {
        "id": uuid.uuid4().hex[:12],
        "category": category,
        "title": ai_title,
        "summary": ai_summary,
        "content": content_text or "(내용 미추출)",
        "date": target_date,
        "weekday": weekday,
        "source_filename": file_name,
        "source_url": source_link.strip() or None,
        "attachment_kind": attachment_kind,
        "tags": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    store.add_curation(item)

    # 벡터스토어에도 추가 인덱싱
    add_curation_to_vectorstore(item)

    return {"status": "ok", "item": _serialize_curation(item)}


@router.get("/assets/{item_id}")
async def open_curation_asset(item_id: str):
    item = next((entry for entry in store.curation_items if entry.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, "항목 없음")

    if item.get("attachment_kind") == "link" and item.get("source_url"):
        return RedirectResponse(item["source_url"])

    file_name = item.get("source_filename")
    if not file_name:
        raise HTTPException(404, "첨부 없음")

    asset_path = CURATION_ASSET_DIR / file_name
    if not asset_path.exists():
        raise HTTPException(404, "파일 없음")

    media_type, _ = mimetypes.guess_type(asset_path.name)
    return FileResponse(asset_path, media_type=media_type or "application/octet-stream")


@router.delete("/items/{item_id}")
async def delete_curation(item_id: str):
    for i, item in enumerate(store.curation_items):
        if item["id"] == item_id:
            file_name = item.get("source_filename")
            if file_name:
                asset_path = CURATION_ASSET_DIR / file_name
                if asset_path.exists():
                    asset_path.unlink()
            store.curation_items.pop(i)
            store._save()
            # 벡터스토어 재빌드 (삭제 후 동기화)
            build_curation_vectorstore(store.curation_items)
            return {"status": "ok"}
    raise HTTPException(404, "항목 없음")


@router.put("/items/{item_id}")
async def update_curation(item_id: str, req: UpdateCurationRequest):
    if _find_curation_by_date(req.date, exclude_item_id=item_id):
        raise HTTPException(400, "해당 날짜에는 이미 다른 큐레이션 자료가 있습니다. 기존 자료를 삭제하거나 다른 날짜를 선택해 주세요.")

    for item in store.curation_items:
        if item["id"] == item_id:
            item["category"] = req.category
            item["date"] = req.date
            item["weekday"] = datetime.strptime(req.date, "%Y-%m-%d").weekday()
            store._save()
            build_curation_vectorstore(store.curation_items)
            return {"status": "ok", "item": _serialize_curation(item)}
    raise HTTPException(404, "항목 없음")
