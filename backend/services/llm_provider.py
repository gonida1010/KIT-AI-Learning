"""
LLM 프로바이더 추상화 — OpenAI ↔ 폐쇄망(On-Premise) LLM 스왑 가능 인터페이스.
환경변수 LLM_PROVIDER 로 "openai" | "onpremise" 전환.
"""

import json
import os
import re
import logging
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger(__name__)


# ── JSON 추출 유틸 ────────────────────────────────────────
def extract_json(text: str) -> dict:
    """LLM 응답에서 JSON 블록 추출."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    raise ValueError("JSON을 파싱할 수 없습니다.")


# ── 추상 인터페이스 ──────────────────────────────────────
class LLMProvider(ABC):
    """모든 에이전트가 사용하는 LLM 인터페이스."""

    @abstractmethod
    async def chat(self, system_prompt: str, user_message: str) -> str: ...

    @abstractmethod
    async def chat_json(self, system_prompt: str, user_message: str) -> dict: ...

    @abstractmethod
    async def chat_with_history(
        self, system_prompt: str, messages: list[dict]
    ) -> str: ...


# ── OpenAI 프로바이더 ────────────────────────────────────
class OpenAIProvider(LLMProvider):
    """OpenAI API (gpt-4o-mini 등)."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        logger.info(f"OpenAI 프로바이더 초기화: {model}")

    async def chat(self, system_prompt: str, user_message: str) -> str:
        res = await self.llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )
        return res.content

    async def chat_json(self, system_prompt: str, user_message: str) -> dict:
        res = await self.llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )
        return extract_json(res.content)

    async def chat_with_history(
        self, system_prompt: str, messages: list[dict]
    ) -> str:
        lc = [SystemMessage(content=system_prompt)]
        for m in messages:
            if m["role"] == "user":
                lc.append(HumanMessage(content=m["content"]))
            else:
                lc.append(AIMessage(content=m["content"]))
        res = await self.llm.ainvoke(lc)
        return res.content


# ── On-Premise 프로바이더 ────────────────────────────────
class OnPremiseProvider(LLMProvider):
    """
    폐쇄망 LLM — vLLM · Ollama · TGI 등 OpenAI 호환 서버.
    환경변수: LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "http://localhost:8000/v1"
        )
        self.model = model or os.getenv("LLM_MODEL", "default")
        _key = api_key or os.getenv("LLM_API_KEY", "not-needed")
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            model=self.model,
            api_key=_key,
            temperature=0.3,
        )
        logger.info(f"OnPremise 프로바이더 초기화: {self.base_url}/{self.model}")

    async def chat(self, system_prompt: str, user_message: str) -> str:
        res = await self.llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )
        return res.content

    async def chat_json(self, system_prompt: str, user_message: str) -> dict:
        res = await self.llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )
        return extract_json(res.content)

    async def chat_with_history(
        self, system_prompt: str, messages: list[dict]
    ) -> str:
        lc = [SystemMessage(content=system_prompt)]
        for m in messages:
            if m["role"] == "user":
                lc.append(HumanMessage(content=m["content"]))
            else:
                lc.append(AIMessage(content=m["content"]))
        res = await self.llm.ainvoke(lc)
        return res.content


# ── 팩토리 ───────────────────────────────────────────────
def create_llm_provider() -> LLMProvider:
    """환경변수 LLM_PROVIDER 에 따라 적절한 프로바이더 생성."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "onpremise":
        return OnPremiseProvider()
    return OpenAIProvider(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
