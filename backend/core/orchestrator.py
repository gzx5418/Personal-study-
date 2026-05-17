from __future__ import annotations

import asyncio
import importlib
import logging
import traceback
from typing import Any

from .agent import BaseAgent
from .context import UnifiedContext
from .stream_bus import StreamBus, StreamEvent, StreamEventType

logger = logging.getLogger("zhixue.orchestrator")

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
    """总控调度器。
    
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
            logger.warning(f"未知的 capability: {capability}，回退到 chat")
            path = CAPABILITY_MAP["chat"]

        module_path, class_name = path.split(":")
        try:
            module = importlib.import_module(module_path)
            agent_cls = getattr(module, class_name)
            agent = agent_cls()
            self._agent_cache[capability] = agent
            return agent
        except (ImportError, AttributeError) as e:
            logger.error(f"加载 Agent 失败: {capability} -> {path}: {e}")
            raise

    async def dispatch(self, ctx: UnifiedContext) -> StreamBus:
        stream = StreamBus()
        stream.emit(StreamEvent(StreamEventType.SESSION, {"session_id": ctx.session_id}))

        capability = ctx.active_capability or "chat"
        agent = self._resolve_agent(capability)

        async def _run():
            try:
                result = await agent.run(ctx, stream)
            except Exception as e:
                logger.error(
                    f"Agent 执行失败: {capability}, session={ctx.session_id}, error={e}",
                    exc_info=True,
                )
                stream.error(f"处理请求时发生错误: {str(e)[:200]}")
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
            logger.error(
                f"同步 Agent 执行失败: {ctx.active_capability}, error={e}",
                exc_info=True,
            )
            return {"success": False, "error": f"处理请求时发生错误: {str(e)[:200]}"}


orchestrator = Orchestrator()
