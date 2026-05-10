from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus
from config import settings


class PathPlannerAgent(BaseAgent):
    """学习路径规划 Agent — 项目核心创新点之一。
    
    基于知识依赖图（DAG）和掌握度，生成个性化学习路径。
    支持自适应调整：掌握度变化后自动更新路径。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="path_planner_agent", module_name="path_planner")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("path_plan", "正在规划学习路径...")

        from services.knowledge_graph import knowledge_graph_service
        from services.mastery_service import mastery_service
        from services.profile_service import profile_service

        course_id = ctx.config_overrides.get("course_id", settings.COURSE_ID)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        profile = profile_service.get_profile(ctx.user_id)

        graph_path = knowledge_graph_service.get_learning_path(course_id, mastery)
        recommended = knowledge_graph_service.get_recommended_next(course_id, mastery)

        prompt = self.load_prompt("plan_path", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "mastery_summary": json.dumps(mastery_service.get_mastery_summary(ctx.user_id), ensure_ascii=False),
            "graph_path": json.dumps(graph_path, ensure_ascii=False, indent=2),
            "recommended": json.dumps(recommended, ensure_ascii=False, indent=2),
            "user_message": ctx.user_message,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ctx.user_message},
        ]

        result = await self.call_llm_json(messages, temperature=0.4)

        result["graph_path"] = graph_path
        result["recommended_next"] = recommended
        result["mastery_summary"] = mastery_service.get_mastery_summary(ctx.user_id)

        stream.result(result)
        stream.stage_end("path_plan")
        return result

    async def generate_path(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        return await self.process(ctx, stream)

    async def adjust_path(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        """根据最新掌握度调整路径。"""
        ctx.user_message = "根据最新学习情况，调整我的学习路径"
        return await self.process(ctx, stream)
