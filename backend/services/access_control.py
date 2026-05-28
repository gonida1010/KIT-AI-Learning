"""Shared role checks for protected dashboard APIs."""

from fastapi import HTTPException

from db.store import store


def require_role(token: str, role: str, *, allow_demo: bool = True) -> dict:
    if not token:
        raise HTTPException(401, "인증 필요")
    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(401, "유효하지 않은 세션")
    user = store.get_user(user_id)
    if not user or user.get("role") != role:
        raise HTTPException(403, f"{role} 권한 필요")
    if not allow_demo and store.get_session_type(token) == "demo":
        raise HTTPException(403, "데모 계정에서는 관리 데이터를 변경할 수 없습니다.")
    return user
