"""
AI 채팅 서비스 — 카카오톡 스타일 지능형 챗봇 로직.
유사도 기반 선택형 응답(Multi-Choice) + 즉각 자료 송부 + 핸드오프.
"""

import json
import re
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """\
당신은 국비지원(KDT) 코딩 학원의 AI 멘토 데스크입니다.
수강생의 질문에 친절하고 정확하게 답변합니다.

[지식 베이스 문맥]
{context}

[응답 규칙]
1. 수강생의 질문이 모호하면 3~4개의 구체적 선택지를 제시하세요.
2. 구체적인 질문에는 즉시 답변하고 관련 자료가 있으면 알려주세요.
3. 감정적/심층 상담이 필요한 경우 멘토 상담을 안내하세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "content": "답변 메시지 텍스트",
  "choices": [
    {{"label": "선택지 제목", "description": "선택지 설명"}}
  ],
  "needs_handoff": false,
  "related_docs": ["관련 자료 이름"]
}}

- choices가 불필요한 경우 빈 배열 []로 설정.
- needs_handoff가 true이면 감정적·심층 상담 필요 케이스.
- related_docs는 언급한 자료/파일명 목록.
"""


def extract_json(text: str) -> dict:
    """LLM 응답에서 JSON만 추출."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start: end + 1])
    raise ValueError("JSON을 찾을 수 없습니다.")


async def generate_chat_response(
    message: str,
    retriever,
    llm: ChatOpenAI,
) -> dict:
    """수강생 메시지에 대한 AI 응답 생성."""
    context = ""
    if retriever:
        docs = retriever.invoke(message[:800])
        context = "\n\n".join(d.page_content for d in docs)

    prompt = CHAT_SYSTEM_PROMPT.format(
        context=context or "(지식 베이스가 아직 비어 있습니다. 일반적인 KDT 과정 지식으로 답변하세요.)"
    )

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=message),
    ])

    try:
        return extract_json(response.content)
    except Exception:
        return {
            "content": response.content,
            "choices": [],
            "needs_handoff": False,
            "related_docs": [],
        }
