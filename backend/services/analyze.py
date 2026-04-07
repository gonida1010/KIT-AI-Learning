"""
Vision / OCR — 이미지에서 코드·텍스트 추출.
CurriMap AI 분석을 위한 LLM 체인.
"""

import base64
import json
import re
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)

# ─── 이미지 → 텍스트 ──────────────────────────────────────
async def extract_text_from_image(
    image_bytes: bytes, mime_type: str, vision_llm: ChatOpenAI,
) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    response = vision_llm.invoke([
        HumanMessage(content=[
            {"type": "text", "text": (
                "이 이미지에 포함된 모든 텍스트와 코드를 추출해 주세요. "
                "코드가 있다면 프로그래밍 언어도 알려 주세요. 텍스트만 출력하세요."
            )},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
        ])
    ])
    return response.content


# ─── CurriMap 분석 체인 ────────────────────────────────────
CURRIMAP_PROMPT = """\
당신은 국비지원 코딩 학원의 AI 학습 내비게이터입니다.
학습자가 올린 코드나 텍스트를 분석하여, 커리큘럼 내에서의 위치와 학습 맥락을 친절하게 설명합니다.

아래는 커리큘럼 문서에서 검색된 관련 정보입니다:
---
{context}
---

분석할 코드/텍스트:
```
{code}
```

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
설명 텍스트 내의 전문 용어는 반드시 <term>용어</term> 형태로 태깅하세요.

{{
  "location": "N개월 차 - 해당 단원/주제명",
  "progress_percentage": 0~100 사이 숫자,
  "why_learn": "이 코드가 무엇인지, 왜 배우는지에 대한 설명 (전문 용어를 <term> 태그로 감쌈)",
  "whats_next": "이 이후에 배울 내용에 대한 설명 (전문 용어를 <term> 태그로 감쌈)",
  "glossary": {{
    "용어1": "쉬운 설명",
    "용어2": "쉬운 설명"
  }}
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
    raise ValueError("LLM 응답에서 JSON을 찾을 수 없습니다.")


async def analyze_code(code_text: str, retriever, llm: ChatOpenAI) -> dict:
    context = ""
    if retriever:
        docs = retriever.invoke(code_text[:1000])
        context = "\n\n".join(d.page_content for d in docs)

    prompt = CURRIMAP_PROMPT.format(
        context=context or "(커리큘럼 문서가 아직 업로드되지 않았습니다. 일반적인 프로그래밍 커리큘럼을 기준으로 답변하세요.)",
        code=code_text[:3000],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return extract_json(response.content)
