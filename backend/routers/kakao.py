"""
카카오 i 오픈빌더 Webhook — 스킬 서버.
웹 챗봇과 동일한 4대 기능 구성:
  1. 오늘의 큐레이션 (행정·커리어)
  2. 조교 연결 (보충수업 예약/취소)
  3. 학습 팁 (멘토 자료)
  4. 멘토 연결 (1:1 상담)
+ 자유 입력 → Main Router AI → Agent A / Agent B / Human Handoff
"""

import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
import re
import traceback

from fastapi import APIRouter, Request

from db.store import store

router = APIRouter(prefix="/api/kakao", tags=["kakao"])
logger = logging.getLogger(__name__)

KAKAO_TEXT_LIMIT = 990  # simpleText 최대 1000자, 여유분 확보
KAKAO_TIMEOUT = 4.5  # 카카오 스킬 타임아웃 5초, 여유분 0.5초

_KST = timezone(timedelta(hours=9))

# 데모용 기본 멘토 ID (시드 데이터와 동일)
_DEFAULT_MENTOR_ID = "mentor_001"

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# ── 웹 챗봇과 동일한 4대 메뉴 키워드 ────────────────────
_WELCOME_KEYWORDS = {"기본상담", "시작", "시작하기", "처음으로", "메뉴", "안녕", "안녕하세요", "하이", "hello", "hi"}
_CURATION_KEYWORDS = {"오늘의 큐레이션", "큐레이션", "뉴스", "채용정보", "IT뉴스", "AI타임스", "자격증", "공모전", "채용", "뉴스 보기"}
_TA_KEYWORDS = {"조교 연결", "조교", "보충수업", "보충 수업", "예약하기", "조교 예약"}
_TIPS_KEYWORDS = {"학습 팁", "학습팁", "멘토 자료", "최신 자료", "기초 자료", "학습자료"}
_MENTOR_KEYWORDS = {"멘토 연결", "멘토님과 직접 상담하기", "멘토 상담 요청", "멘토 상담", "1:1 상담"}
_CANCEL_KEYWORDS = {"예약 취소", "예약취소", "취소하기", "취소"}


def _now():
    return datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S")


def _uid():
    return uuid.uuid4().hex[:12]


def _resolve_student(kakao_user_id: str) -> str:
    """카카오 사용자 ID → 내부 student_id 생성/확인.
    신규 유저는 자동으로 기본 멘토에 배정 (데모용).
    기존 유저 중 mentor_id가 없으면 자동 배정.
    """
    student_id = f"kakao_{kakao_user_id}"
    existing = store.get_user(student_id)
    if not existing:
        store.create_user({
            "id": student_id, "kakao_id": kakao_user_id,
            "name": f"카카오 유저 ({kakao_user_id[:8]})",
            "profile_image": "", "role": "student",
            "mentor_id": _DEFAULT_MENTOR_ID, "invite_code": None,
            "career_pref": None, "created_at": _now(),
        })
    elif not existing.get("mentor_id"):
        store.update_user(student_id, {"mentor_id": _DEFAULT_MENTOR_ID})
    return student_id


# ── SkillResponse 빌더 ──────────────────────────────────
def _truncate(text: str, limit: int = KAKAO_TEXT_LIMIT) -> str:
    """simpleText 1000자 제한 안전 보장."""
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def simple_text(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": _truncate(text)}}]}}


def text_with_quick_replies(text: str, choices: list[dict], show_handoff: bool = True) -> dict:
    qr = []
    for c in choices:
        qr.append({
            "messageText": c.get("messageText", c.get("label", "")),
            "action": "message",
            "label": c.get("label", ""),
        })
    if show_handoff:
        qr.append({"messageText": "멘토 연결", "action": "message", "label": "🙋‍♂️ 멘토 연결"})
    # quickReplies 최대 10개
    qr = qr[:10]
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": _truncate(text)}}], "quickReplies": qr}}


def _main_menu_response(student_name: str = "") -> dict:
    """웹 챗봇의 4버튼 웰컴 화면과 동일한 메뉴 응답."""
    greeting = f"안녕하세요 {student_name}님!" if student_name else "안녕하세요!"
    text = f"{greeting}\n아래 메뉴를 선택하거나, 궁금한 점을 바로 입력해 주세요."
    return text_with_quick_replies(text, [
        {"label": "📰 오늘의 큐레이션", "messageText": "오늘의 큐레이션"},
        {"label": "📅 조교 연결", "messageText": "조교 연결"},
        {"label": "📚 학습 팁", "messageText": "학습 팁"},
    ], show_handoff=True)


# ── 메인 웹훅 ────────────────────────────────────────────
@router.post("/webhook")
async def kakao_webhook(request: Request):
    try:
        return await _kakao_webhook_inner(request)
    except Exception as e:
        logger.error(f"카카오 웹훅 처리 오류: {e}\n{traceback.format_exc()}")
        return simple_text("죄송합니다, 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")


async def _kakao_webhook_inner(request: Request):
    from main import retriever, llm_provider
    from services.agent_router import classify_intent
    from services.agent_a import handle_agent_a
    from services.agent_b import handle_agent_b

    body = await request.json()
    logger.info(f"카카오 웹훅: {body}")

    user_request = body.get("userRequest", {})
    utterance = user_request.get("utterance", "").strip()
    kakao_user_id = user_request.get("user", {}).get("id", "unknown")

    if not utterance:
        return simple_text("메시지를 입력해 주세요.")

    student_id = _resolve_student(kakao_user_id)
    student = store.get_user(student_id) or {}
    student_name = student.get("name", "")

    # ── 1) 웰컴/메뉴 (웹 챗봇 4버튼과 동일) ──
    if utterance in _WELCOME_KEYWORDS:
        return _main_menu_response(student_name)

    # ── 2) 오늘의 큐레이션 (웹의 "오늘의 큐레이션" 버튼과 동일) ──
    if utterance in _CURATION_KEYWORDS:
        return await _handle_curation(student_id, utterance)

    # ── 3) 조교 연결 — 예약/취소 선택 (웹의 "조교 연결" 버튼과 동일) ──
    if utterance in _TA_KEYWORDS:
        return _handle_ta_menu()

    # ── 3-a) 예약하기 → 바로 날짜 목록 ──
    if utterance == "예약하기":
        return _handle_booking_dates()

    # ── 3-b) 예약 취소 ──
    if utterance in _CANCEL_KEYWORDS:
        return _handle_cancel_list(student_id)

    # ── 4) 학습 팁 (웹의 "학습 팁" 버튼과 동일) ──
    if utterance in _TIPS_KEYWORDS:
        return _handle_tips_menu()

    if utterance == "최신 자료 보기":
        return await _handle_tips(student_id, "latest")

    if utterance == "기초 자료 보기":
        return await _handle_tips(student_id, "basic")

    # ── 5) 멘토 연결 (웹의 "멘토 연결" 버튼과 동일) ──
    if utterance in _MENTOR_KEYWORDS:
        return _handle_mentor_handoff(student_id)

    # ── 예약 플로우: 날짜 선택 ──
    booking_date_match = re.match(r"^예약날짜:(\d{4}-\d{2}-\d{2})$", utterance)
    if booking_date_match:
        return _handle_booking_date(booking_date_match.group(1))

    # ── 예약 플로우: 시간 선택 ──
    booking_slot_match = re.match(r"^예약:(?P<slot_id>[a-f0-9]{12})$", utterance)
    if booking_slot_match:
        slot_id = booking_slot_match.group("slot_id")
        slot = next((s for s in store.get_available_slots() if s.get("id") == slot_id), None)
        if not slot:
            return simple_text("선택한 시간이 더 이상 예약 가능하지 않습니다. 다시 확인해 주세요.")
        return simple_text(
            f"선택한 시간: {slot['ta_name']} | {slot['date']} {slot['start_time']}~{slot['end_time']}\n\n"
            f"어떤 내용을 보충받고 싶으신지 간단히 적어 주세요.\n"
            f"(이름/연락처도 함께 보내시면 조교에게 전달됩니다)\n\n"
            f"예시: 예약정보:{slot_id}:홍길동 / 010-1234-5678 / 파이썬 클래스 self가 헷갈려요\n"
            f"또는: 예약설명:{slot_id}:파이썬 클래스 self가 헷갈려요"
        )

    # ── 예약 플로우: 설명 입력 → 예약 확정 ──
    booking_desc_match = re.match(r"^예약설명:(?P<slot_id>[a-f0-9]{12}):(?P<desc>.+)$", utterance)
    booking_info_match = re.match(
        r"^예약정보:(?P<slot_id>[a-f0-9]{12}):(?P<name>[^/]+?)\s*/\s*(?P<phone>[^/]+?)\s*/\s*(?P<desc>.+)$",
        utterance,
    )
    if booking_desc_match or booking_info_match:
        return await _handle_booking_confirm(student_id, booking_info_match, booking_desc_match)

    # ── 예약 취소 확정 ──
    cancel_match = re.match(r"^예약취소:(?P<slot_id>[a-f0-9]{12})$", utterance)
    if cancel_match:
        return _handle_cancel_confirm(student_id, cancel_match.group("slot_id"))

    # ── 자유 입력 → 에이전트 라우팅 (웹 챗봇과 동일) ──
    store.add_message(student_id, {
        "id": _uid(), "user_id": student_id, "channel": "kakao",
        "role": "user", "agent_type": None,
        "content": utterance, "choices": None, "metadata": None,
        "created_at": _now(),
    })
    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": utterance[:60], "detail": "카카오톡 대화",
    })

    # 카카오 스킬 타임아웃(5초) 방지를 위해 asyncio.wait_for 사용
    try:
        result = await asyncio.wait_for(
            _process_free_input(utterance, student_id, student, retriever, llm_provider,
                                classify_intent, handle_agent_a, handle_agent_b),
            timeout=KAKAO_TIMEOUT,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"카카오 타임아웃: {utterance[:40]}")
        store.add_message(student_id, {
            "id": _uid(), "user_id": student_id, "channel": "kakao",
            "role": "assistant", "agent_type": "agent_a",
            "content": "처리 시간이 초과되었습니다.", "choices": None,
            "metadata": None, "created_at": _now(),
        })
        return text_with_quick_replies(
            "죄송합니다, 응답 생성에 시간이 걸리고 있습니다.\n"
            "잠시 후 다시 시도하시거나 아래 메뉴를 이용해 주세요.",
            [
                {"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"},
                {"label": "📅 조교 연결", "messageText": "조교 연결"},
                {"label": "📚 학습 팁", "messageText": "학습 팁"},
            ],
            show_handoff=True,
        )


async def _process_free_input(utterance, student_id, student, retriever, llm_provider,
                              classify_intent, handle_agent_a, handle_agent_b):
    """자유 입력 처리 — 타임아웃 래핑 대상."""
    routing = await classify_intent(utterance, llm_provider)
    intent = routing["intent"]

    if intent == "human_handoff":
        store.add_handoff({
            "id": _uid(), "student_id": student_id,
            "student_name": student.get("name", ""),
            "reason": "AI 감정 상담 필요 감지",
            "last_message": utterance,
            "priority": "high", "status": "pending", "created_at": _now(),
        })
        store.add_message(student_id, {
            "id": _uid(), "user_id": student_id, "channel": "kakao",
            "role": "assistant", "agent_type": "human_handoff",
            "content": "멘토 상담 대기열에 등록되었습니다.", "choices": None,
            "metadata": None, "created_at": _now(),
        })
        return simple_text(
            "말씀하신 내용을 멘토님께 전달했습니다. 😊\n"
            "담당 멘토님이 최대한 빠르게 연락드리겠습니다."
        )

    if intent == "agent_b":
        ai_result = await handle_agent_b(utterance, llm_provider, student_id)
    else:
        ai_result = await handle_agent_a(utterance, retriever, llm_provider, student_id)

    content = ai_result.get("content", "죄송합니다, 오류가 발생했습니다.")
    choices = ai_result.get("choices", [])

    store.add_message(student_id, {
        "id": _uid(), "user_id": student_id, "channel": "kakao",
        "role": "assistant", "agent_type": intent,
        "content": content, "choices": choices or None,
        "metadata": {"routing": routing}, "created_at": _now(),
    })

    if ai_result.get("needs_handoff"):
        store.add_handoff({
            "id": _uid(), "student_id": student_id,
            "student_name": student.get("name", ""),
            "reason": "AI 감정 상담 감지", "last_message": utterance,
            "priority": "high", "status": "pending", "created_at": _now(),
        })

    # 응답 후 항상 메인 메뉴 바로가기 제공
    menu_qr = [
        {"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"},
        {"label": "📅 조교 연결", "messageText": "조교 연결"},
        {"label": "📚 학습 팁", "messageText": "학습 팁"},
    ]
    if choices:
        for c in choices:
            menu_qr.insert(0, {"label": c.get("label", ""), "messageText": c.get("label", "")})
    return text_with_quick_replies(content, menu_qr[:9], show_handoff=True)


# ══════════════════════════════════════════════════════════
# 기능별 핸들러 (웹 챗봇과 1:1 대응)
# ══════════════════════════════════════════════════════════

# ── 1. 오늘의 큐레이션 ───────────────────────────────────
async def _handle_curation(student_id: str, utterance: str) -> dict:
    """웹 챗봇의 fetchTodayCuration과 동일 — 오늘 등록된 큐레이션 반환."""
    today = datetime.now(_KST).strftime("%Y-%m-%d")
    items = store.get_curations(date=today)

    if not items:
        items = sorted(store.curation_items, key=lambda x: x.get("date", ""), reverse=True)[:5]

    if not items:
        return text_with_quick_replies(
            f"오늘({today}) 등록된 큐레이션이 아직 없습니다.\n관리자가 콘텐츠를 준비 중이에요!",
            [
                {"label": "📅 조교 연결", "messageText": "조교 연결"},
                {"label": "📚 학습 팁", "messageText": "학습 팁"},
            ],
            show_handoff=True,
        )

    lines = [f"📰 오늘의 큐레이션 ({len(items)}건)\n"]
    for item in items[:5]:
        lines.append(f"📌 [{item.get('category', '')}] {item.get('title', '')}")
        if item.get("summary"):
            lines.append(f"   {item['summary']}")
        lines.append(f"   📅 {item.get('date', '')}")
        lines.append("")

    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": "오늘의 큐레이션 조회", "detail": "카카오톡",
    })

    return text_with_quick_replies(
        "\n".join(lines),
        [
            {"label": "📋 채용정보 더보기", "messageText": "채용정보"},
            {"label": "📰 IT뉴스 더보기", "messageText": "IT뉴스"},
            {"label": "🏆 자격증·공모전", "messageText": "자격증"},
            {"label": "📅 조교 연결", "messageText": "조교 연결"},
        ],
        show_handoff=True,
    )


# ── 2. 조교 연결 메뉴 ────────────────────────────────────
def _handle_ta_menu() -> dict:
    """웹 챗봇의 startBookingFlow와 동일 — 예약/취소 선택."""
    return text_with_quick_replies(
        "조교 보충수업을 도와드리겠습니다.\n원하시는 메뉴를 선택해 주세요.",
        [
            {"label": "예약하기", "messageText": "예약하기"},
            {"label": "취소하기", "messageText": "예약 취소"},
        ],
        show_handoff=True,
    )


# ── 2-a. 예약: 날짜 목록 (웹의 fetchBookingDates와 동일) ──
@router.post("/webhook/schedule")
async def kakao_schedule_webhook(request: Request):
    try:
        body = await request.json()
        return _handle_booking_dates()
    except Exception as e:
        logger.error(f"스케줄 웹훅 오류: {e}\n{traceback.format_exc()}")
        return simple_text("죄송합니다, 예약 정보를 불러오는 중 오류가 발생했습니다.")


def _handle_booking_dates() -> dict:
    """웹의 /api/chat/booking/dates와 동일 로직."""
    slots = store.get_available_slots()
    date_map: dict[str, int] = {}
    for s in slots:
        d = s["date"]
        date_map[d] = date_map.get(d, 0) + 1
    dates = sorted(date_map.keys())

    if not dates:
        return text_with_quick_replies(
            "현재 예약 가능한 시간이 없습니다.\n조교 선생님이 일정을 등록하면 안내해 드릴게요.",
            [{"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"}, {"label": "📚 학습 팁", "messageText": "학습 팁"}],
            show_handoff=True,
        )

    lines = ["📅 예약 가능한 날짜를 선택해 주세요.\n"]
    choices = []
    for d in dates[:7]:
        dt = datetime.strptime(d, "%Y-%m-%d")
        wd = WEEKDAY_KR[dt.weekday()]
        count = date_map[d]
        lines.append(f"  • {d} ({wd}) — {count}개 시간대")
        choices.append({"label": f"{d} ({wd})", "messageText": f"예약날짜:{d}"})

    return text_with_quick_replies("\n".join(lines), choices, show_handoff=True)


def _handle_booking_date(date: str) -> dict:
    """웹의 /api/chat/booking/slots?date=와 동일 — 특정 날짜 시간대 표시."""
    slots = store.get_available_slots()
    filtered = [s for s in slots if s["date"] == date]
    filtered.sort(key=lambda s: s.get("start_time", ""))

    if not filtered:
        return text_with_quick_replies(
            f"{date}에는 가능한 시간대가 없습니다. 다른 날짜를 선택해 주세요.",
            [{"label": "다른 날짜 보기", "messageText": "예약하기"}],
            show_handoff=True,
        )

    lines = [f"📅 {date} 예약 가능 시간:\n"]
    choices = []
    for s in filtered[:8]:
        label = f"{s['start_time']}~{s['end_time']} ({s.get('ta_name', '')})"
        lines.append(f"  • {label}")
        choices.append({"label": label, "messageText": f"예약:{s['id']}"})

    return text_with_quick_replies("\n".join(lines) + "\n\n원하는 시간을 선택해 주세요.", choices, show_handoff=True)


# ── 2-b. 예약 확정 (웹의 booking_confirm과 동일) ──
async def _handle_booking_confirm(student_id: str, info_match, desc_match) -> dict:
    from main import llm_provider
    from services.agent_b import generate_briefing_report, normalize_booking_request

    if info_match:
        slot_id = info_match.group("slot_id")
        input_name = info_match.group("name").strip()
        phone = info_match.group("phone").strip()
        description = info_match.group("desc").strip()
    else:
        slot_id = desc_match.group("slot_id")
        input_name = ""
        phone = ""
        description = desc_match.group("desc").strip()

    student = store.get_user(student_id)
    slot = next((s for s in store.get_available_slots() if s.get("id") == slot_id), None)
    if not slot:
        return simple_text("선택한 시간이 더 이상 예약 가능하지 않습니다. 다시 예약 목록을 확인해 주세요.")

    normalized = await normalize_booking_request(
        input_name or (student or {}).get("name", "수강생"),
        phone, description, llm_provider,
    )
    if student and normalized["student_name"] and student.get("name", "").startswith("카카오 유저"):
        store.update_user(student_id, {"name": normalized["student_name"]})

    events = store.get_student_events(student_id)
    keywords = [e["content"] for e in events if e.get("event_type") == "search"]
    briefing = await generate_briefing_report(
        student_name=normalized["student_name"],
        raw_input=normalized["cleaned_request"],
        search_history=keywords,
        llm=llm_provider,
    )
    booked = store.book_slot(
        slot_id=slot_id,
        student_id=student_id,
        student_name=normalized["student_name"],
        desc=normalized["cleaned_request"],
        briefing=briefing,
        student_phone=normalized["student_phone"],
        summary=normalized["short_summary"],
    )
    if not booked:
        return simple_text("예약 처리 중 시간이 마감되었습니다. 다시 시도해 주세요.")

    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "doc_access",
        "content": f"조교 보충수업 예약 ({booked['ta_name']})",
        "detail": normalized["short_summary"][:80],
    })
    return text_with_quick_replies(
        f"✅ 예약 완료되었습니다!\n"
        f"- 시간: {booked['date']} {booked['start_time']}~{booked['end_time']}\n"
        f"- 조교: {booked['ta_name']}\n"
        f"- 연락처: {normalized['student_phone'] or '미입력'}\n"
        f"- 공부 내용: {normalized['cleaned_request']}\n\n"
        f"조교 대시보드에는 요약된 브리핑도 함께 전달됩니다.",
        [
            {"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"},
            {"label": "📚 학습 팁", "messageText": "학습 팁"},
        ],
        show_handoff=True,
    )


# ── 2-c. 예약 취소 목록 (웹의 startCancelFlow와 동일) ──
def _handle_cancel_list(student_id: str) -> dict:
    """웹의 /api/chat/booking/my와 동일 — 학생의 예약 목록 표시."""
    booked = store.get_booked_slots_by_student(student_id)
    if not booked:
        return text_with_quick_replies(
            "현재 예약된 보충수업이 없습니다.",
            [{"label": "예약하기", "messageText": "예약하기"}, {"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"}],
            show_handoff=True,
        )

    lines = ["취소할 예약을 선택해 주세요.\n"]
    choices = []
    for s in booked[:5]:
        label = f"{s.get('date', '')} {s.get('start_time', '')}~{s.get('end_time', '')} ({s.get('ta_name', '')})"
        lines.append(f"  • {label}")
        desc = s.get("booking_description", "")
        if desc:
            lines.append(f"    내용: {desc[:30]}")
        choices.append({"label": label, "messageText": f"예약취소:{s['id']}"})

    return text_with_quick_replies("\n".join(lines), choices, show_handoff=False)


def _handle_cancel_confirm(student_id: str, slot_id: str) -> dict:
    """웹의 /api/chat/booking/cancel과 동일."""
    slot = store.cancel_booking(slot_id, student_id)
    if not slot:
        return simple_text("취소할 수 없는 예약입니다. 다시 확인해 주세요.")

    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "booking_cancel",
        "content": f"조교 보충수업 취소 ({slot.get('ta_name', '')})",
        "detail": f"{slot.get('date', '')} {slot.get('start_time', '')}~{slot.get('end_time', '')}",
    })
    return text_with_quick_replies(
        f"❌ 예약이 취소되었습니다.\n"
        f"- {slot.get('date', '')} {slot.get('start_time', '')}~{slot.get('end_time', '')} ({slot.get('ta_name', '')})",
        [
            {"label": "다시 예약하기", "messageText": "예약하기"},
            {"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"},
        ],
        show_handoff=True,
    )


# ── 3. 학습 팁 (웹의 fetchLearningTips/fetchTipsByType과 동일) ──
def _handle_tips_menu() -> dict:
    """웹 챗봇과 동일 — 최신 자료/기초 자료 선택."""
    return text_with_quick_replies(
        "어떤 자료를 보고 싶으신가요?",
        [
            {"label": "최신 자료", "messageText": "최신 자료 보기"},
            {"label": "기초 자료", "messageText": "기초 자료 보기"},
        ],
        show_handoff=True,
    )


async def _handle_tips(student_id: str, tips_type: str) -> dict:
    """웹의 /api/chat/tips와 동일 — 멘토 자료 반환."""
    student = store.get_user(student_id)
    mentor_id = (student or {}).get("mentor_id")

    if not mentor_id:
        return text_with_quick_replies(
            "아직 연결된 멘토가 없습니다.\n학원에 문의해 주세요.",
            [{"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"}, {"label": "📅 조교 연결", "messageText": "조교 연결"}],
            show_handoff=True,
        )

    mentor = store.get_user(mentor_id)
    mentor_name = (mentor or {}).get("name", "")

    if tips_type == "basic":
        docs = store.get_mentor_basic_docs(mentor_id, limit=5)
        type_label = "기초"
    else:
        docs = store.get_mentor_docs(mentor_id, limit=5)
        type_label = "최신"

    if not docs:
        return text_with_quick_replies(
            f"아직 {mentor_name} 멘토님이 올린 {type_label} 자료가 없습니다.",
            [{"label": "📰 큐레이션", "messageText": "오늘의 큐레이션"}, {"label": "📅 조교 연결", "messageText": "조교 연결"}],
            show_handoff=True,
        )

    lines = [f"📚 {mentor_name} 멘토님의 {type_label} 자료 ({len(docs)}건)\n"]
    for d in docs:
        title = d.get("digest_title") or d.get("filename", "자료")
        summary = d.get("digest_summary", "")
        lines.append(f"📎 {title}")
        if summary:
            lines.append(f"   {summary[:60]}")
        lines.append("")

    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "chat",
        "content": f"{type_label} 자료 조회", "detail": "카카오톡",
    })

    return text_with_quick_replies(
        "\n".join(lines),
        [
            {"label": "최신 자료" if tips_type == "basic" else "기초 자료",
             "messageText": "최신 자료 보기" if tips_type == "basic" else "기초 자료 보기"},
            {"label": "📅 조교 연결", "messageText": "조교 연결"},
        ],
        show_handoff=True,
    )


# ── 4. 멘토 연결 (웹의 requestMentorHandoff와 동일) ──
def _handle_mentor_handoff(student_id: str) -> dict:
    """웹의 /api/chat/handoff와 동일."""
    student = store.get_user(student_id) or {}
    last_msgs = store.get_conversation(student_id)
    last_user_msg = ""
    for m in reversed(last_msgs):
        if m.get("role") == "user":
            last_user_msg = m["content"]
            break
    store.add_handoff({
        "id": _uid(), "student_id": student_id,
        "student_name": student.get("name", ""),
        "reason": "카카오톡 멘토 상담 요청",
        "last_message": last_user_msg or "(대화 없음)",
        "priority": "medium", "status": "pending", "created_at": _now(),
    })
    store.add_event(student_id, {
        "timestamp": _now(), "event_type": "handoff",
        "content": "멘토 상담 요청", "detail": (last_user_msg or "카카오톡")[:80],
    })
    return simple_text(
        "✅ 멘토 상담 대기열에 등록되었습니다.\n"
        "담당 멘토님이 최대한 빠르게 연락드리겠습니다.\n"
        "혼자 고민하지 마시고 편하게 기다려 주세요."
    )


# ── 큐레이션 조회 전용 블록 (오픈빌더 스킬 블록용) ────────
@router.post("/webhook/curation")
async def kakao_curation_webhook(request: Request):
    """카테고리별 큐레이션 정보 제공."""
    try:
        body = await request.json()
        action_params = body.get("action", {}).get("params", {})
        category = action_params.get("category", "")
        kakao_user_id = body.get("userRequest", {}).get("user", {}).get("id", "unknown")
        student_id = _resolve_student(kakao_user_id)

        categories = [c.strip() for c in category.split(",") if c.strip()] if category else []

        if categories:
            items = []
            for cat in categories:
                items.extend(store.get_curations(category=cat))
        else:
            items = store.curation_items

        items = sorted(items, key=lambda x: x.get("date", ""), reverse=True)[:5]

        if not items:
            return simple_text("해당 카테고리의 정보가 아직 없습니다.")

        lines = []
        for item in items:
            lines.append(f"📌 [{item['category']}] {item['title']}")
            lines.append(f"   {item['summary']}")
            lines.append(f"   📅 {item['date']}")
            lines.append("")

        return text_with_quick_replies(
            "\n".join(lines),
            [
                {"label": "📋 채용정보 더보기", "messageText": "채용정보"},
                {"label": "📰 IT뉴스 더보기", "messageText": "IT뉴스"},
                {"label": "🏆 자격증·공모전", "messageText": "자격증"},
                {"label": "📅 조교 연결", "messageText": "조교 연결"},
            ],
            show_handoff=True,
        )
    except Exception as e:
        logger.error(f"큐레이션 웹훅 오류: {e}\n{traceback.format_exc()}")
        return simple_text("죄송합니다, 큐레이션 정보를 불러오는 중 오류가 발생했습니다.")


# ── 연결 테스트용 엔드포인트 ─────────────────────────────
@router.post("/webhook/test")
async def kakao_test_webhook(request: Request):
    """스킬 연결 확인용 — 즉시 응답."""
    body = await request.json()
    utterance = body.get("userRequest", {}).get("utterance", "")
    return simple_text(f"✅ 스킬 서버 연결 성공!\n발화: {utterance}")
