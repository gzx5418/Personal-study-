from __future__ import annotations

import abc
import json
import threading
from typing import Any, AsyncGenerator, Type

from .context import UnifiedContext
from .stream_bus import StreamBus


class BaseAgent(abc.ABC):
    """所有 Agent 的基类。
    
    提供统一的 LLM 调用接口、Prompt 加载、Token 追踪。
    子类只需实现 process() 方法。
    """

    capabilities: list[str] = []

    def __init__(
        self,
        agent_name: str,
        module_name: str = "default",
        language: str = "zh",
        model: str | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.module_name = module_name
        self.language = language
        self.model = model
        self._llm_service = None
        self._prompt_manager = None

    @property
    def llm_service(self):
        if self._llm_service is None:
            from services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    @property
    def prompt_manager(self):
        if self._prompt_manager is None:
            from services.prompt_manager import prompt_manager
            self._prompt_manager = prompt_manager
        return self._prompt_manager

    def load_prompt(self, prompt_name: str, variables: dict[str, str] | None = None) -> str:
        template = self.prompt_manager.get_prompt(self.module_name, prompt_name, self.language)
        if variables:
            for k, v in variables.items():
                template = template.replace(f"{{{{{k}}}}}", v)
        return template

    async def call_llm(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict | None = None,
    ) -> str:
        return await self.llm_service.chat(
            messages=messages,
            model=model or self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    async def call_llm_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
    ) -> dict | list:
        text = await self.call_llm(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            raise

    async def stream_llm(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.llm_service.stream_chat(
            messages=messages,
            model=model or self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    @abc.abstractmethod
    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        ...

    async def run(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        token = self.llm_service.push_request_options(ctx.config_overrides)
        stream.agent_start(self.agent_name, getattr(self, '_capability', self.agent_name))
        try:
            return await self.process(ctx, stream)
        except Exception as e:
            stream.error(f"[{self.agent_name}] {str(e)}")
            raise
        finally:
            stream.agent_end(self.agent_name, getattr(self, '_capability', self.agent_name))
            self.llm_service.pop_request_options(token)


class AgentRegistry:
    _instance: AgentRegistry | None = None
    _lock = threading.Lock()

    def __new__(cls) -> AgentRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._agents: dict[str, Type[BaseAgent]] = {}
                cls._instance._instances: dict[str, BaseAgent] = {}
            return cls._instance

    def register(self, capability: str, agent_class: Type[BaseAgent]) -> None:
        self._agents[capability] = agent_class

    def get_agent(self, capability: str) -> BaseAgent:
        if capability not in self._instances:
            agent_class = self._agents.get(capability)
            if agent_class is None:
                raise KeyError(f"未注册的 capability: {capability}")
            self._instances[capability] = agent_class()
        return self._instances[capability]

    def has_capability(self, capability: str) -> bool:
        return capability in self._agents

    def list_capabilities(self) -> list[str]:
        return list(self._agents.keys())

    def clear(self) -> None:
        self._agents.clear()
        self._instances.clear()


def register_agent(capability: str):
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        agent_registry.register(capability, cls)
        return cls
    return decorator


agent_registry = AgentRegistry()
