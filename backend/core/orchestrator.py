from __future__ import annotations

import asyncio
import importlib
import logging
import traceback
from typing import Any

from .agent import BaseAgent, agent_registry
from .context import UnifiedContext
from .stream_bus import StreamBus, StreamEvent, StreamEventType

logger = logging.getLogger("zhixue.orchestrator")

_AGENT_MODULES = [
    "agents.chat_agent",
    "agents.deep_solve",
    "agents.profiler",
    "agents.profile_builder",
    "agents.diagnostic",
    "agents.resource_planner",
    "agents.generator",
    "agents.path_planner",
    "agents.evaluator",
    "agents.safety",
]

# 关键 Agent 模块：导入失败时必须抛出异常，避免静默回退导致核心能力缺失
_CRITICAL_AGENT_MODULES = {
    "agents.chat_agent",
}


class Orchestrator:
    """总控调度器。
    
    负责：
    1. 解析用户意图，确定 Capability
    2. 创建 StreamBus，调度对应 Agent
    3. 返回事件流给前端
    """

    def __init__(self) -> None:
        self._modules_loaded = False

    def _load_agent_modules(self) -> None:
        if self._modules_loaded:
            return
        for module_path in _AGENT_MODULES:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                if module_path in _CRITICAL_AGENT_MODULES:
                    logger.error(
                        f"关键 Agent 模块加载失败: {module_path}: {e}",
                        exc_info=True,
                    )
                    raise
                logger.error(f"加载 Agent 模块失败: {module_path}: {e}")
        self._modules_loaded = True

    def _resolve_agent(self, capability: str) -> BaseAgent:
        self._load_agent_modules()
        if agent_registry.has_capability(capability):
            return agent_registry.get_agent(capability)
        logger.warning(f"未知的 capability: {capability}，回退到 chat")
        return agent_registry.get_agent("chat")

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
