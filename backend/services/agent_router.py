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
1. "agent_a" — 행정/커리어 질문: 취업, 채용 공고, IT 뉴스, AI 뉴스, 자격증, 공모전, 학원 규정, 포트폴리오, 이력서, 면접, 자료 요청, 큐레이션, 일반 질문, 인사말, 모호한 짧은 입력
2. "agent_b" — 학습/기술 질문: 코딩, 프로그래밍, 자바, 파이썬, 클래스, 함수, SQL, HTML, CSS, JavaScript, React, 알고리즘, 자료구조, 데이터베이스, API, 디버깅, 에러 해결, 코드 리뷰 등 기술적 질문
3. "human_handoff" — 멘토 직접 상담: 감정적 힘듦, 슬럼프, 동기 부족, 진로 깊은 고민, 자퇴/중단 고려, 대인관계 문제 등 정서적 케어

❗ 중요 규칙:
- 판단이 애매하면 반드시 agent_a로 분류하세요.
- "?", "네", "아니요", "처음부터", "다시" 같은 짧은 입력은 agent_a입니다.
- 프로그래밍/코딩 관련 단어가 있으면 agent_b입니다.
- human_handoff는 명확히 감정적 고통이 느껴질 때만 사용하세요. confidence 0.8 이상일 때만.

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
