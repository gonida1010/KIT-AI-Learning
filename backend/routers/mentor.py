"""멘토 API — 대시보드, 학생 관리, 멘토 전용 지식 베이스."""

import mimetypes
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from langchain.schema import Document

from db.store import store
from models.schemas import StudentProfile, TimelineEvent
from services.rag import DATA_DIR, add_mentor_document_to_vectorstore

router = APIRouter(prefix="/api/mentor", tags=["mentor"])
MENTOR_ASSET_DIR = DATA_DIR / "mentor_assets"


def _require_mentor(token: str) -> dict:
    if not token:
        raise HTTPException(401, "인증 필요")
    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(401, "유효하지 않은 세션")
    user = store.get_user(user_id)
    if not user or user.get("role") != "mentor":
        raise HTTPException(403, "멘토 권한 필요")
    return user


def _doc_is_stale(uploaded_at: str) -> bool:
    if not uploaded_at:
        return False
    try:
        return datetime.now() - datetime.fromisoformat(uploaded_at) > timedelta(days=14)
    except ValueError:
        return False


async def _build_ai_digest(raw_text: str, fallback_name: str) -> tuple[str, str]:
    from main import llm_provider

    cleaned = (raw_text or "").strip()
    if not cleaned:
        cleaned = fallback_name

    prompt = """
당신은 멘토 전용 학습자료 정리 비서입니다.
원문을 읽고 수강생에게 보여주기 좋은 짧은 제목과 요약을 만드세요.

반드시 아래 JSON 형식으로만 답변하세요:
{
  "title": "짧은 제목",
  "summary": "한두 문장 요약"
}
"""

    if llm_provider:
        try:
            result = await llm_provider.chat_json(prompt, cleaned[:4000])
            title = (result.get("title") or "").strip()
            summary = (result.get("summary") or "").strip()
            if title and summary:
                return title[:80], summary[:220]
        except Exception:
            pass

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    title = lines[0][:60] if lines else Path(fallback_name).stem
    summary = " ".join(lines[1:4])[:180] if len(lines) > 1 else f"{title} 관련 멘토 자료"
    return title or Path(fallback_name).stem, summary or f"{fallback_name} 관련 멘토 자료"


def _serialize_mentor_doc(doc: dict) -> dict:
    data = dict(doc)
    if data.get("source_kind") == "link":
        data["attachment_url"] = data.get("source_url")
    else:
        data["attachment_url"] = f"/api/mentor/knowledge/assets/{data['id']}"
    data["is_stale"] = _doc_is_stale(data.get("uploaded_at", ""))
    return data


@router.get("/dashboard")
async def mentor_dashboard(token: str = ""):
    mentor = _require_mentor(token)
    today = datetime.now().strftime("%Y-%m-%d")
    today_curations = store.get_curations(date=today)[:3]
    recent_docs = store.get_mentor_docs(mentor["id"])[:5]
    activity = store.get_recent_chat_activity(mentor["id"], hours=24)[:20]
    ta_bookings = store.get_ta_bookings_for_mentor(mentor["id"])[:8]

    return {
        "today_curations": today_curations,
        "recent_docs": [_serialize_mentor_doc(doc) for doc in recent_docs],
        "recent_activity": activity,
        "ta_bookings": ta_bookings,
    }


@router.get("/students/by-mentor/{mentor_id}")
async def list_students_by_mentor(mentor_id: str):
    return store.get_students_by_mentor(mentor_id)


@router.get("/student/{student_id}/timeline")
async def student_timeline(student_id: str):
    student = store.get_user(student_id)
    if not student:
        raise HTTPException(404, "학생 없음")
    events = store.get_student_events(student_id)
    keywords = [e["content"] for e in events if e["event_type"] == "search"]
    return StudentProfile(
        id=student_id,
        name=student["name"],
        career_pref=student.get("career_pref", ""),
        events=[TimelineEvent(**e) for e in events],
        frequent_keywords=keywords,
    )


@router.get("/knowledge")
async def list_mentor_knowledge(token: str = "", q: str = "", scope: str = "all", limit: int = 50):
    mentor = _require_mentor(token)
    docs = store.get_mentor_docs(mentor["id"], query=q)
    if scope == "latest":
        docs = [doc for doc in docs if not _doc_is_stale(doc.get("uploaded_at", ""))]
    elif scope == "stale":
        docs = [doc for doc in docs if _doc_is_stale(doc.get("uploaded_at", ""))]
    return [_serialize_mentor_doc(doc) for doc in docs[:limit]]


@router.post("/knowledge/upload")
async def upload_mentor_knowledge(
    token: str = Form(""),
    file: UploadFile | None = File(default=None),
    source_link: str = Form(""),
):
    mentor = _require_mentor(token)
    if file is None and not source_link.strip():
        raise HTTPException(400, "파일 또는 링크가 필요합니다.")

    mentor_dir = MENTOR_ASSET_DIR / mentor["id"]
    mentor_dir.mkdir(parents=True, exist_ok=True)

    source_kind = "link" if source_link.strip() and file is None else "file"
    content_text = ""
    stored_name = ""

    if file is not None:
        if not file.filename:
            raise HTTPException(400, "파일명 없음")
        stored_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
        stored_path = mentor_dir / stored_name
        payload = await file.read()
        stored_path.write_bytes(payload)
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
                source_kind = "image"
    else:
        content_text = f"외부 링크 자료: {source_link.strip()}"

    digest_title, digest_summary = await _build_ai_digest(content_text, stored_name or source_link)
    mentor_doc_id = uuid.uuid4().hex[:12]
    mentor_doc = {
        "id": mentor_doc_id,
        "mentor_id": mentor["id"],
        "filename": stored_name or source_link.strip(),
        "source_filename": stored_name or None,
        "source_url": source_link.strip() or None,
        "source_kind": source_kind,
        "digest_title": digest_title,
        "digest_summary": digest_summary,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "chunk_count": max(1, len(content_text) // 600 + 1 if content_text else 1),
    }
    store.add_mentor_doc(mentor_doc)

    vector_text = (
        f"제목: {digest_title}\n"
        f"요약: {digest_summary}\n"
        f"원문: {content_text or digest_title}"
    )
    add_mentor_document_to_vectorstore(
        mentor["id"],
        [
            Document(
                page_content=vector_text,
                metadata={
                    "mentor_doc_id": mentor_doc_id,
                    "digest_title": digest_title,
                    "filename": mentor_doc["filename"],
                },
            )
        ],
    )

    return {"status": "ok", "document": _serialize_mentor_doc(mentor_doc)}


@router.delete("/knowledge/{doc_id}")
async def delete_mentor_knowledge(doc_id: str, token: str = ""):
    mentor = _require_mentor(token)
    removed = store.remove_mentor_doc(mentor["id"], doc_id)
    if not removed:
        raise HTTPException(404, "문서 없음")

    source_filename = removed.get("source_filename")
    if source_filename:
        asset_path = MENTOR_ASSET_DIR / mentor["id"] / source_filename
        if asset_path.exists():
            asset_path.unlink()
    return {"status": "ok"}


@router.get("/knowledge/assets/{doc_id}")
async def open_mentor_asset(doc_id: str):
    doc = store.get_mentor_doc(doc_id)
    if not doc:
        raise HTTPException(404, "문서 없음")

    if doc.get("source_kind") == "link" and doc.get("source_url"):
        return RedirectResponse(doc["source_url"])

    file_name = doc.get("source_filename")
    if not file_name:
        raise HTTPException(404, "첨부 없음")

    asset_path = MENTOR_ASSET_DIR / doc["mentor_id"] / file_name
    if not asset_path.exists():
        raise HTTPException(404, "파일 없음")

    media_type, _ = mimetypes.guess_type(asset_path.name)
    return FileResponse(asset_path, media_type=media_type or "application/octet-stream")


# ── 초대 링크 ────────────────────────────────────────────
@router.post("/invite")
async def create_invite(mentor_id: str = "mentor_001"):
    mentor = store.get_user(mentor_id)
    if not mentor or mentor["role"] != "mentor":
        raise HTTPException(404, "멘토 없음")
    code = mentor.get("invite_code")
    if not code:
        code = uuid.uuid4().hex[:8].upper()
        store.update_user(mentor_id, {"invite_code": code})
    store.set_invite_code(code, mentor_id)
    return {"invite_code": code, "invite_url": f"/?invite={code}"}
