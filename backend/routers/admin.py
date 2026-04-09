"""관리자 대시보드 API — 공통 큐레이션만 관리."""

from fastapi import APIRouter

from db.store import store

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/curations")
async def list_all_curations():
    items = sorted(store.curation_items, key=lambda x: x.get("date", ""), reverse=True)
    return items
