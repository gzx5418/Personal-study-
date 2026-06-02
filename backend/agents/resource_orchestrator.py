# -*- coding: utf-8 -*-
"""资源编排智能体 — 协调多个子 Agent 完成个性化资源生成。

协作链:
  ResourceOrchestratorAgent
    → ResourceSubAgent (lecture/quiz/mindmap/code_lab/reading/animation/ppt)
    → SafetyAgent (内容安全审查)
"""
from __future__ import annotations

import logging
from typing import Any

from core.agent import BaseAgent, register_agent, agent_registry
from core.context import UnifiedContext
from core.stream_bus import StreamBus

logger = logging.getLogger(__name__)

# resource_type → sub-agent capability
_TYPE_TO_CAPABILITY = {
    "lecture": "gen_lecture",
    "quiz": "gen_quiz",
    "mindmap": "gen_mindmap",
    "code_lab": "gen_code_lab",
    "code": "gen_code_lab",
    "extended_reading": "gen_reading",
    "reading": "gen_reading",
    "animation": "gen_animation",
    "video": "gen_animation",
    "ppt_outline": "gen_ppt",
    "ppt": "gen_ppt",
}


@register_agent("resource_orchestrator")
class ResourceOrchestratorAgent(BaseAgent):
    """资源编排智能体。

    根据请求的资源类型，调度对应的子 Agent 执行生成，
    再调用 SafetyAgent 进行安全审查，形成完整的多智能体协作链。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="resource_orchestrator", module_name="resource_planner")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        requested_type = ctx.config_overrides.get("resource_type", "lecture")
        capability = _TYPE_TO_CAPABILITY.get(requested_type, requested_type)
        topic = ctx.config_overrides.get("topic", "")

        stream.stage_start(
            "resource_orchestrator",
            f"资源编排器: 正在协调{requested_type}资源生成...",
        )
        stream.thinking(
            f"资源编排器启动 → 调度 {capability} 子智能体\n"
            f"资源类型: {requested_type} | 主题: {topic}"
        )

        # --- 1. 调度子 Agent ---
        if not agent_registry.has_capability(capability):
            stream.thinking(f"子智能体 {capability} 未注册，回退到通用 generate 智能体")
            capability = "generate"

        sub_agent = agent_registry.get_agent(capability)
        sub_result = await sub_agent.run(ctx, stream)

        # --- 2. 安全审查（如果子 Agent 未内置） ---
        safety_result = sub_result.get("safety")
        if not safety_result or safety_result.get("review_skipped"):
            try:
                from agents.safety import SafetyAgent
                safety_agent = SafetyAgent()
                content = sub_result.get("content", "")
                sources = sub_result.get("sources_used", [])
                safety_result = await safety_agent.review_content(
                    content, requested_type, sources,
                )
                stream.thinking(
                    f"[ResourceOrchestrator] 安全审查完成: "
                    f"{'通过' if safety_result.get('is_safe', True) else '发现问题'}"
                )
            except Exception as exc:
                logger.warning("Safety review in orchestrator failed: %s", exc)
                safety_result = {
                    "is_safe": None, "review_skipped": True,
                    "issues": [], "suggestions": ["编排层安全审查未完成"],
                }

        # --- 3. 汇总结果 ---
        result = {
            **sub_result,
            "orchestrated_by": "resource_orchestrator",
            "agents_involved": [
                {"name": "resource_orchestrator", "role": "编排调度"},
                {"name": sub_agent.agent_name, "role": f"{requested_type}资源生成"},
                {"name": "safety_agent", "role": "内容安全审查"},
            ],
            "safety": safety_result,
        }
        stream.result(result)
        stream.stage_end("resource_orchestrator")
        return result
