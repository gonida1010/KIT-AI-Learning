"""
하이브리드 인증 — 카카오 OAuth + QR 로그인 + 초대 링크 연동.
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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def _now():
    return datetime.now().isoformat(timespec="seconds")


# ── Request schemas ──────────────────────────────────────
class KakaoCallbackReq(BaseModel):
    code: str
    invite_code: str | None = None


class QRApproveReq(BaseModel):
    qr_token: str
    session_token: str


class LinkMentorReq(BaseModel):
    invite_code: str


# ── 카카오 OAuth ─────────────────────────────────────────
@router.get("/kakao/login-url")
async def kakao_login_url():
    if not KAKAO_REST_API_KEY:
        raise HTTPException(500, "KAKAO_REST_API_KEY 미설정")
    url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return {"login_url": url}


@router.post("/kakao/callback")
async def kakao_callback(req: KakaoCallbackReq):
    if not KAKAO_REST_API_KEY:
        raise HTTPException(500, "KAKAO_REST_API_KEY 미설정")

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
        raise HTTPException(400, "카카오 토큰 발급 실패")
    access_token = token_res.json().get("access_token")
    if not access_token:
        raise HTTPException(400, "Access Token 누락")

    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_res.status_code != 200:
        raise HTTPException(400, "사용자 정보 조회 실패")

    kakao_user = user_res.json()
    kakao_id = str(kakao_user.get("id", ""))
    profile = kakao_user.get("kakao_account", {}).get("profile", {})
    nickname = profile.get("nickname", f"유저_{kakao_id[:6]}")
    profile_image = profile.get("profile_image_url", "")

    user = store.get_user_by_kakao_id(kakao_id)
    if not user:
        mentor_id = None
        if req.invite_code and req.invite_code in store.invite_codes:
            mentor_id = store.invite_codes[req.invite_code]
        user = store.create_user({
            "id": uuid.uuid4().hex[:12],
            "kakao_id": kakao_id,
            "name": nickname,
            "profile_image": profile_image,
            "role": "student",
            "mentor_id": mentor_id,
            "invite_code": None,
            "career_pref": None,
            "created_at": _now(),
        })
        logger.info(f"신규 가입: {nickname} (kakao {kakao_id})")
    else:
        user["name"] = nickname
        user["profile_image"] = profile_image
        if req.invite_code and req.invite_code in store.invite_codes and not user.get("mentor_id"):
            user["mentor_id"] = store.invite_codes[req.invite_code]
        store._save()

    token = uuid.uuid4().hex
    store.create_session(token, user["id"], "kakao")

    return {
        "token": token,
        "user": {
            "id": user["id"], "name": user["name"],
            "role": user["role"], "profile_image": user.get("profile_image", ""),
        },
    }


# ── QR 로그인 ────────────────────────────────────────────
@router.post("/qr/generate")
async def qr_generate():
    """PC에서 QR 코드 표시용 세션 생성."""
    qr_token = uuid.uuid4().hex[:16]
    store.qr_sessions[qr_token] = {
        "status": "pending",
        "user_id": None,
        "session_token": None,
        "created_at": _now(),
    }
    store._save()
    return {
        "qr_token": qr_token,
        "qr_url": f"{FRONTEND_URL}/?qr_approve={qr_token}",
    }


@router.get("/qr/check")
async def qr_check(token: str):
    """PC에서 QR 상태 폴링."""
    qr = store.qr_sessions.get(token)
    if not qr:
        raise HTTPException(404, "QR 세션 없음")
    if qr["status"] == "approved" and qr.get("session_token"):
        user = store.get_user(qr["user_id"])
        return {
            "status": "approved",
            "token": qr["session_token"],
            "user": {
                "id": user["id"], "name": user["name"],
                "role": user["role"],
                "profile_image": user.get("profile_image", ""),
            },
        }
    return {"status": qr["status"]}


@router.post("/qr/approve")
async def qr_approve(req: QRApproveReq):
    """모바일에서 QR 스캔 후 승인."""
    qr = store.qr_sessions.get(req.qr_token)
    if not qr:
        raise HTTPException(404, "QR 세션 없음")
    if qr["status"] != "pending":
        raise HTTPException(400, "이미 처리된 QR")

    user_id = store.get_session(req.session_token)
    if not user_id:
        raise HTTPException(401, "모바일 인증 필요")

    new_token = uuid.uuid4().hex
    store.create_session(new_token, user_id, "qr")
    qr["status"] = "approved"
    qr["user_id"] = user_id
    qr["session_token"] = new_token
    store._save()
    return {"status": "ok"}


# ── 세션 ─────────────────────────────────────────────────
@router.get("/me")
async def get_me(token: str = ""):
    if not token:
        raise HTTPException(401, "인증 필요")
    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(401, "유효하지 않은 세션")
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(401, "사용자 없음")
    return {
        "id": user["id"], "name": user["name"],
        "role": user["role"], "profile_image": user.get("profile_image", ""),
    }


@router.post("/role")
async def update_role(token: str = "", role: str = ""):
    if not token:
        raise HTTPException(401, "인증 필요")
    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(401, "유효하지 않은 세션")
    if role not in ("student", "mentor", "ta", "admin"):
        raise HTTPException(400, "유효하지 않은 역할")
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(404, "사용자 없음")
    user["role"] = role
    store._save()
    return {"status": "ok", "role": role}


@router.post("/logout")
async def logout(token: str = ""):
    if token:
        store.delete_session(token)
    return {"status": "ok"}


# ── 초대 링크 연동 ────────────────────────────────────────
@router.post("/link-mentor")
async def link_mentor(req: LinkMentorReq, token: str = ""):
    """초대 코드로 수강생과 멘토를 매핑."""
    if not token:
        raise HTTPException(401, "인증 필요")
    user_id = store.get_session(token)
    if not user_id:
        raise HTTPException(401, "유효하지 않은 세션")
    mentor_id = store.invite_codes.get(req.invite_code)
    if not mentor_id:
        raise HTTPException(404, "유효하지 않은 초대 코드")
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(404, "사용자 없음")
    user["mentor_id"] = mentor_id
    store._save()
    return {"status": "ok", "mentor_id": mentor_id}


# ── 데모 로그인 ──────────────────────────────────────────
@router.post("/demo")
async def demo_login(role: str = "student"):
    if role not in ("student", "mentor", "ta", "admin"):
        raise HTTPException(400, "유효하지 않은 역할")
    demo_users = {"student": "student_001", "mentor": "mentor_001", "ta": "ta_jung", "admin": "admin_001"}
    uid = demo_users.get(role, "student_001")
    user = store.get_user(uid)
    if not user:
        raise HTTPException(500, "데모 유저 없음")
    token = uuid.uuid4().hex
    store.create_session(token, uid, "demo")
    return {
        "token": token,
        "user": {
            "id": user["id"], "name": user["name"],
            "role": user["role"], "profile_image": user.get("profile_image", ""),
        },
    }
