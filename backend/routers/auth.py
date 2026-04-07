"""
카카오 OAuth 2.0 로그인 — 인가 코드 → Access Token → 사용자 정보.
"""

import os
import uuid
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.store import store

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:3000/oauth/callback")


class KakaoCallbackRequest(BaseModel):
    code: str  # 카카오 인가 코드


@router.get("/kakao/login-url")
async def kakao_login_url():
    """프론트에서 카카오 로그인 페이지로 리다이렉트할 URL 반환."""
    if not KAKAO_REST_API_KEY:
        raise HTTPException(status_code=500, detail="KAKAO_REST_API_KEY가 설정되지 않았습니다.")
    url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return {"login_url": url}


@router.post("/kakao/callback")
async def kakao_callback(req: KakaoCallbackRequest):
    """
    카카오 인가 코드로 Access Token을 발급받고, 사용자 정보를 가져와 로그인 처리.
    """
    if not KAKAO_REST_API_KEY:
        raise HTTPException(status_code=500, detail="KAKAO_REST_API_KEY가 설정되지 않았습니다.")

    # 1) 인가 코드 → Access Token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": KAKAO_REST_API_KEY,
                "redirect_uri": KAKAO_REDIRECT_URI,
                "code": req.code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        logger.error(f"카카오 토큰 발급 실패: {token_res.text}")
        raise HTTPException(status_code=400, detail="카카오 토큰 발급에 실패했습니다.")

    token_data = token_res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Access Token을 받지 못했습니다.")

    # 2) Access Token → 사용자 정보
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_res.status_code != 200:
        logger.error(f"카카오 사용자 정보 조회 실패: {user_res.text}")
        raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다.")

    kakao_user = user_res.json()
    kakao_id = str(kakao_user.get("id", ""))
    kakao_account = kakao_user.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    nickname = profile.get("nickname", f"유저_{kakao_id[:6]}")
    profile_image = profile.get("profile_image_url", "")

    # 3) 우리 DB에 사용자 등록/조회
    user = store.get_user_by_kakao_id(kakao_id)
    if not user:
        # 신규 가입 — 기본 역할: student
        user = store.create_user({
            "id": uuid.uuid4().hex[:12],
            "kakao_id": kakao_id,
            "name": nickname,
            "profile_image": profile_image,
            "role": "student",  # student | mentor | ta
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        logger.info(f"신규 사용자 가입: {nickname} ({kakao_id})")
    else:
        # 기존 사용자 — 프로필 업데이트
        user["name"] = nickname
        user["profile_image"] = profile_image
        store._save()

    # 세션 토큰 생성 (데모용 — 프로덕션에서는 JWT 사용)
    session_token = uuid.uuid4().hex
    store.create_session(session_token, user["id"])

    return {
        "token": session_token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "role": user["role"],
            "profile_image": user.get("profile_image", ""),
        },
    }


@router.get("/me")
async def get_me(token: str = ""):
    """세션 토큰으로 현재 사용자 정보 조회."""
    if not token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다.")

    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    return {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "profile_image": user.get("profile_image", ""),
    }


@router.post("/role")
async def update_role(token: str = "", role: str = ""):
    """사용자 역할 변경 (demo용 — 프로덕션에서는 관리자만 가능)."""
    if not token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다.")

    if role not in ("student", "mentor", "ta"):
        raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다.")

    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    user["role"] = role
    store._save()

    return {"status": "ok", "role": role}


@router.post("/logout")
async def logout(token: str = ""):
    """세션 삭제."""
    if token:
        store.delete_session(token)
    return {"status": "ok"}
