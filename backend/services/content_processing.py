import json
import logging
import re
from html import unescape
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

MAX_DIGEST_SOURCE_CHARS = 9000
MAX_VECTOR_SOURCE_CHARS = 12000
MAX_EXCERPT_CHARS = 900
_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".xml",
    ".yml",
    ".yaml",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".sql",
    ".log",
}


def normalize_source_text(text: str, limit: int | None = None) -> str:
    cleaned = unescape(text or "")
    cleaned = cleaned.replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\u00a0", " ", cleaned)
    cleaned = cleaned.strip()
    if limit and len(cleaned) > limit:
        return cleaned[:limit].rstrip()
    return cleaned


def build_source_excerpt(raw_text: str, limit: int = MAX_EXCERPT_CHARS) -> str:
    cleaned = normalize_source_text(raw_text)
    if not cleaned:
        return ""

    parts = [segment.strip() for segment in re.split(r"\n\n+", cleaned) if segment.strip()]
    excerpt_parts: list[str] = []
    current_len = 0
    for part in parts:
        if len(part) < 20 and excerpt_parts:
            continue
        remaining = limit - current_len
        if remaining <= 0:
            break
        chunk = part[:remaining].strip()
        if not chunk:
            continue
        excerpt_parts.append(chunk)
        current_len += len(chunk) + 2
    excerpt = "\n\n".join(excerpt_parts)
    return excerpt[:limit].rstrip()


def fallback_digest(raw_text: str, fallback_name: str) -> tuple[str, str]:
    cleaned = normalize_source_text(raw_text)
    lines = [line.strip(" -•\t") for line in cleaned.splitlines() if line.strip()]
    title = lines[0][:70] if lines else Path(fallback_name).stem

    detail_lines = [line for line in lines[1:] if len(line) > 12]
    if detail_lines:
        summary = " ".join(detail_lines[:3])[:320]
    elif cleaned:
        summary = cleaned[:320]
    else:
        summary = f"{title} 관련 자료"

    return title or Path(fallback_name).stem, summary or f"{fallback_name} 관련 자료"


async def build_ai_digest(
    raw_text: str,
    fallback_name: str,
    llm_provider,
    assistant_role: str,
) -> tuple[str, str]:
    cleaned = normalize_source_text(raw_text)
    if not cleaned:
        return fallback_digest("", fallback_name)

    prompt = f"""
당신은 {assistant_role}입니다.
아래 원문을 직접 읽고, 실제 본문에 근거한 제목과 요약을 만드세요.

규칙:
1. 제목만 보고 추정하지 말고 본문 핵심 내용을 반영하세요.
2. summary 는 2~4문장으로 작성하고, 중요한 사실·조건·절차·주의사항·수치 중 핵심을 압축하세요.
3. 본문에 없는 일반론, 홍보 문구, 추상적 표현을 추가하지 마세요.
4. 가능하면 학생/멘토가 바로 행동할 수 있는 정보가 드러나게 정리하세요.

반드시 아래 JSON 형식으로만 답변하세요:
{{
  "title": "짧고 명확한 제목",
  "summary": "본문 핵심이 살아있는 밀도 높은 요약"
}}
"""

    if not llm_provider:
        return fallback_digest(cleaned, fallback_name)

    try:
        result = await llm_provider.chat_json(
            prompt,
            cleaned[:MAX_DIGEST_SOURCE_CHARS],
        )
        title = normalize_source_text(result.get("title") or "", limit=90)
        summary = normalize_source_text(result.get("summary") or "", limit=360)
        if title and summary:
            return title, summary
    except Exception:
        logger.exception("AI digest build failed")

    return fallback_digest(cleaned, fallback_name)


def build_vector_text(title: str, summary: str, source_excerpt: str, raw_text: str) -> str:
    cleaned = normalize_source_text(raw_text, limit=MAX_VECTOR_SOURCE_CHARS)
    excerpt = source_excerpt or build_source_excerpt(cleaned)
    return (
        f"제목: {title}\n"
        f"요약: {summary}\n"
        f"핵심 원문 발췌:\n{excerpt or '(발췌 없음)'}\n\n"
        f"원문:\n{cleaned or title}"
    )


def _decode_bytes(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="ignore")


def _html_to_text(html: str) -> str:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = normalize_source_text(title_match.group(1)) if title_match else ""
    body = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
    body = re.sub(r"<!--([\s\S]*?)-->", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = normalize_source_text(body)
    if title and body and not body.startswith(title):
        return f"{title}\n\n{body}"
    return body or title


def _extract_file_text(file_path: Path, original_filename: str) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return normalize_source_text("\n".join(pages))

    if suffix == ".docx":
        try:
            from docx import Document

            doc = Document(str(file_path))
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            return normalize_source_text("\n".join(paragraphs))
        except Exception:
            logger.exception("DOCX text extraction failed")

    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return f"첨부 파일명: {Path(original_filename).stem}"

    if suffix in _TEXT_EXTENSIONS:
        payload = file_path.read_bytes()
        text = _decode_bytes(payload)
        if suffix in {".html", ".htm", ".xml"}:
            return _html_to_text(text)
        if suffix == ".json":
            try:
                return normalize_source_text(json.dumps(json.loads(text), ensure_ascii=False, indent=2))
            except Exception:
                return normalize_source_text(text)
        return normalize_source_text(text)

    try:
        payload = file_path.read_bytes()
        return normalize_source_text(_decode_bytes(payload))
    except Exception:
        logger.exception("Generic file text extraction failed")
        return f"첨부 파일명: {Path(original_filename).stem}"


async def _fetch_url_text(source_link: str) -> str:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10.0,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; Edu-Sync-AI/3.0; +https://example.local)",
        },
    ) as client:
        response = await client.get(source_link)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "html" in content_type:
            return _html_to_text(response.text)
        if "json" in content_type:
            try:
                return normalize_source_text(
                    json.dumps(response.json(), ensure_ascii=False, indent=2)
                )
            except Exception:
                return normalize_source_text(response.text)
        return normalize_source_text(response.text)


async def extract_source_text(
    file_path: Path | None,
    original_filename: str,
    source_link: str,
) -> str:
    if file_path and file_path.exists():
        text = _extract_file_text(file_path, original_filename)
        if text:
            return text

    if source_link.strip():
        try:
            text = await _fetch_url_text(source_link.strip())
            if text:
                return text
        except Exception:
            logger.exception("URL text extraction failed")
        return f"외부 링크 자료: {source_link.strip()}"

    return f"첨부 파일명: {Path(original_filename).stem}"