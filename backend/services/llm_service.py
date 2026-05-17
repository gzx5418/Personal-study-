from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import AsyncGenerator

from openai import AsyncOpenAI

from config import settings


@dataclass
class TokenStats:
    """Token 使用统计。"""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_requests: int = 0
    history: deque = field(default_factory=lambda: deque(maxlen=200))

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    def record(self, prompt_tokens: int, completion_tokens: int, model: str, agent: str = ""):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_requests += 1
        self.history.append({
            "timestamp": time.time(),
            "model": model,
            "agent": agent,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        })

    def to_dict(self) -> dict:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
        }


class TraceEvent:
    """Trace 事件 — 记录每次 LLM 调用的详情。"""
    def __init__(self):
        self._events: list[dict] = []

    def record(self, event_type: str, agent: str, data: dict):
        self._events.append({
            "type": event_type,
            "agent": agent,
            "timestamp": time.time(),
            **data,
        })

    def get_events(self, limit: int = 50) -> list[dict]:
        return self._events[-limit:]

    def clear(self):
        self._events.clear()


class LLMService:
    """统一 LLM 调用服务。
    
    增强功能：
    - Token 使用追踪
    - Trace 回调（记录每次调用的 agent、model、token 用量）
    - 自动重试（429/5xx）
    """

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self.token_stats = TokenStats()
        self.trace = TraceEvent()
        self._request_options: ContextVar[dict] = ContextVar("llm_request_options", default={})

    def push_request_options(self, options: dict | None):
        allowed_keys = {"llm_model", "reasoning_model", "vision_model", "embedding_model"}
        filtered = {
            key: value.strip()
            for key, value in (options or {}).items()
            if key in allowed_keys and isinstance(value, str) and value.strip()
        }
        return self._request_options.set(filtered)

    def pop_request_options(self, token) -> None:
        self._request_options.reset(token)

    def get_request_option(self, key: str, default: str = "") -> str:
        return self._request_options.get().get(key, default)

    def resolve_chat_model(self, explicit_model: str | None = None) -> str:
        return explicit_model or self.get_request_option("llm_model") or settings.LLM_MODEL

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_HOST,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict | None = None,
        agent_name: str = "",
        max_retries: int = 3,
    ) -> str:
        kwargs: dict = {
            "model": self.resolve_chat_model(model),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        last_error = None
        for attempt in range(max_retries):
            try:
                resp = await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs),
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                )
                content = resp.choices[0].message.content or ""

                if resp.usage:
                    self.token_stats.record(
                        prompt_tokens=resp.usage.prompt_tokens,
                        completion_tokens=resp.usage.completion_tokens,
                        model=kwargs["model"],
                        agent=agent_name,
                    )
                    self.trace.record("llm_call", agent_name, {
                        "model": kwargs["model"],
                        "prompt_tokens": resp.usage.prompt_tokens,
                        "completion_tokens": resp.usage.completion_tokens,
                    })

                return self._clean_response(content)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.trace.record("llm_retry", agent_name, {
                        "attempt": attempt + 1,
                        "error": str(e)[:200],
                        "wait_seconds": wait_time,
                    })
                    await asyncio.sleep(wait_time)

        raise last_error

    @staticmethod
    def _clean_response(text: str) -> str:
        import re
        text = re.sub(r'<\|begin_of_box\|>', '', text)
        text = re.sub(r'<\|end_of_box\|>', '', text)
        text = re.sub(r'<\|begin_of_thought\|>[\s\S]*?<\|end_of_thought\|>', '', text)
        text = re.sub(r'<\|im_start\|>|<\|im_end\|>', '', text)
        return text.strip()

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        agent_name: str = "",
    ) -> AsyncGenerator[str, None]:
        resolved_model = self.resolve_chat_model(model)
        stream = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=resolved_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            ),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

        self.trace.record("llm_stream", agent_name, {
            "model": resolved_model,
        })

    def get_stats(self) -> dict:
        return {
            "token_stats": self.token_stats.to_dict(),
            "recent_traces": self.trace.get_events(limit=20),
        }


llm_service = LLMService()
