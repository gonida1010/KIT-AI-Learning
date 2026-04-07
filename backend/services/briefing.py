"""
AI 브리핑 서비스 — 조교 보충수업 계획서 자동 생성.
수강생의 막말 입력 → AI가 구조화된 브리핑 리포트로 변환.
"""

import json
import re
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

BRIEFING_PROMPT = """\
당신은 국비지원 코딩 학원의 AI 학습 분석 어시스턴트입니다.
수강생의 보충 수업 요청과 이력을 분석하여, 조교(TA)에게 전달할 구조화된 브리핑 리포트를 생성합니다.

[수강생 정보]
이름: {student_name}
최근 챗봇 검색/활동 이력: {search_history}

[수강생 원본 요청]
"{raw_input}"

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "student_name": "{student_name}",
  "search_history": "최근 검색/활동 키워드를 요약한 한 줄 문장",
  "core_need": "핵심 필요 내용 (구체적인 학습 주제)",
  "ai_recommendation": "AI 추천 지도 방향 (2~3문장)"
}}
"""


def extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start: end + 1])
    raise ValueError("JSON을 찾을 수 없습니다.")


async def generate_briefing_report(
    student_name: str,
    raw_input: str,
    search_history: list[str],
    llm: ChatOpenAI,
) -> dict:
    """수강생의 자유 입력을 조교용 브리핑 리포트로 변환."""
    history_str = ", ".join(search_history) if search_history else "이력 없음"

    prompt = BRIEFING_PROMPT.format(
        student_name=student_name,
        search_history=history_str,
        raw_input=raw_input,
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        return extract_json(response.content)
    except Exception:
        return {
            "student_name": student_name,
            "search_history": history_str,
            "core_need": raw_input,
            "ai_recommendation": "AI 분석에 실패했습니다. 수강생 원본 요청을 참고해 주세요.",
        }
