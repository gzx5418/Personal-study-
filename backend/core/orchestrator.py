from __future__ import annotations

import asyncio
import importlib
from typing import Any

from .agent import BaseAgent
from .context import UnifiedContext
from .stream_bus import StreamBus, StreamEvent, StreamEventType


CAPABILITY_MAP = {
    "chat": "agents.chat_agent:ChatAgent",
    "deep_solve": "agents.deep_solve:DeepSolveAgent",
    "profile": "agents.profiler:ProfilerAgent",
    "profile_build": "agents.profile_builder:ProfileBuilderAgent",
    "diagnostic": "agents.diagnostic:DiagnosticAgent",
    "resource_plan": "agents.resource_planner:ResourcePlannerAgent",
    "generate": "agents.generator:GeneratorAgent",
    "path_plan": "agents.path_planner:PathPlannerAgent",
    "evaluate": "agents.evaluator:EvaluatorAgent",
    "safety": "agents.safety:SafetyAgent",
}


class Orchestrator:
    """总控调度器，参考 DeepTutor ChatOrchestrator 设计。
    
    负责：
    1. 解析用户意图，确定 Capability
    2. 创建 StreamBus，调度对应 Agent
    3. 返回事件流给前端
    """

    def __init__(self) -> None:
        self._agent_cache: dict[str, BaseAgent] = {}

    def _resolve_agent(self, capability: str) -> BaseAgent:
        if capability in self._agent_cache:
            return self._agent_cache[capability]

        path = CAPABILITY_MAP.get(capability)
        if not path:
            path = CAPABILITY_MAP["chat"]

        module_path, class_name = path.split(":")
        module = importlib.import_module(module_path)
        agent_cls = getattr(module, class_name)
        agent = agent_cls()
        self._agent_cache[capability] = agent
        return agent

    async def dispatch(self, ctx: UnifiedContext) -> StreamBus:
        stream = StreamBus()
        stream.emit(StreamEvent(StreamEventType.SESSION, {"session_id": ctx.session_id}))

        capability = ctx.active_capability or "chat"
        agent = self._resolve_agent(capability)

        async def _run():
            try:
                result = await agent.run(ctx, stream)
            except Exception as e:
                stream.error(str(e))
            finally:
                stream.done()

        asyncio.create_task(_run())
        return stream

    async def dispatch_sync(self, ctx: UnifiedContext) -> dict[str, Any]:
        stream = StreamBus()
        agent = self._resolve_agent(ctx.active_capability or "chat")
        try:
            result = await agent.run(ctx, stream)
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}


orchestrator = Orchestrator()
