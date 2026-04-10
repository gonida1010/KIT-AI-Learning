"""
메인 라우터 AI — 사용자 의도를 분류하여 적절한 하위 에이전트로 분배.
intent: "agent_a" | "agent_b" | "human_handoff"
"""

import logging
from services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """\
You are an intent-classification router for a Korean government-funded (KDT) coding bootcamp.
Analyze the user's message and determine which downstream agent should handle it.

Classification criteria:
1. "agent_a" — Administrative & career questions: job postings, hiring info, IT/AI news, certifications, competitions, bootcamp policies, portfolio/resume reviews, interview prep, document requests, curated content, and any general non-technical questions.
2. "agent_b" — TA scheduling & technical learning: supplementary lesson booking, programming questions, code debugging, technical concept explanations, TA consultation requests, and any hands-on learning-related queries.
3. "human_handoff" — Direct mentor counseling: emotional support, burnout/slump, lack of motivation, deep career anxiety, considering dropout, interpersonal issues, or any situation requiring empathetic human conversation.

IMPORTANT: Respond ONLY with the JSON below. Do NOT include any other text.
{
  "intent": "agent_a" | "agent_b" | "human_handoff",
  "confidence": 0.0 ~ 1.0,
  "reason": "One-line classification rationale in Korean"
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
