"""
메인 라우터 AI — 사용자 의도를 분류하여 적절한 하위 에이전트로 분배.
intent: "agent_a" | "agent_b" | "human_handoff"
"""

import logging
from services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """\
당신은 KDT 코딩 학원의 AI 라우터입니다.
사용자 메시지의 의도를 분석하여 적절한 처리 에이전트를 결정합니다.

분류 기준:
1. "agent_a" — 행정/커리어 질문: 취업, 채용 공고, IT 뉴스, AI 뉴스, 자격증, 공모전, 학원 규정, 포트폴리오, 이력서, 면접, 자료 요청, 큐레이션 콘텐츠, 수업 외 일반 질문
2. "agent_b" — 조교 스케줄링: 보충 수업 예약, 수업 내용 기술 질문, 코드 질문, 프로그래밍 학습 질문, 조교 상담 요청
3. "human_handoff" — 멘토 직접 상담: 감정적 상담, 슬럼프, 동기 부족, 진로 깊은 고민, 자퇴/중단 고려, 대인관계 문제 등 정서적 케어

반드시 아래 JSON 형식으로만 응답하세요:
{
  "intent": "agent_a" | "agent_b" | "human_handoff",
  "confidence": 0.0 ~ 1.0,
  "reason": "분류 근거 한 줄 요약"
}
"""


async def classify_intent(message: str, llm: LLMProvider) -> dict:
    """사용자 메시지를 분류하여 에이전트 라우팅 결정."""
    try:
        result = await llm.chat_json(ROUTER_SYSTEM_PROMPT, message)
        intent = result.get("intent", "agent_a")
        if intent not in ("agent_a", "agent_b", "human_handoff"):
            intent = "agent_a"
        return {
            "intent": intent,
            "confidence": float(result.get("confidence", 0.5)),
            "reason": result.get("reason", ""),
        }
    except Exception as e:
        logger.error(f"의도 분류 실패: {e}")
        return {"intent": "agent_a", "confidence": 0.3, "reason": "분류 실패 — 기본값"}
