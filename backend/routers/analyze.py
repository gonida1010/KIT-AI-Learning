"""CurriMap AI — 파일 분석 API (드래그 앤 드롭 진척도 나침반)."""

from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.analyze import extract_text_from_image, analyze_code

router = APIRouter(prefix="/api", tags=["analyze"])

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
CODE_EXTENSIONS = {".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".json", ".sql", ".ipynb"}


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """파일을 받아 커리큘럼 분석 결과 JSON을 반환."""
    from main import retriever, llm, vision_llm  # lazy import

    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = Path(file.filename).suffix.lower()
    content_bytes = await file.read()

    if not content_bytes:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    if ext in IMAGE_EXTENSIONS:
        mime = file.content_type or "image/png"
        code_text = await extract_text_from_image(content_bytes, mime, vision_llm)
    elif ext in CODE_EXTENSIONS or ext == ".txt":
        code_text = content_bytes.decode("utf-8", errors="replace")
    else:
        try:
            code_text = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    try:
        result = await analyze_code(code_text, retriever, llm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {e}")

    return result
