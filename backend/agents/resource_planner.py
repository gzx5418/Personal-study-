from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


@register_agent("resource_plan")
class ResourcePlannerAgent(BaseAgent):
    """资源规划 Agent — 根据学生画像和薄弱点规划资源生成方案。"""

    def __init__(self) -> None:
        super().__init__(agent_name="resource_planner_agent", module_name="resource_planner")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("resource_plan", "正在规划学习资源...")

        from services.profile_service import profile_service
        from services.mastery_service import mastery_service
        from services.knowledge_graph import knowledge_graph_service

        profile = profile_service.get_profile(ctx.user_id)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        course_id = ctx.config_overrides.get("course_id", settings.COURSE_ID)
        graph = knowledge_graph_service.get_all_nodes(course_id)

        prompt = self.load_prompt("plan", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "mastery": json.dumps(mastery, ensure_ascii=False, indent=2),
            "knowledge_graph": json.dumps(graph[:50], ensure_ascii=False, indent=2),
            "user_message": ctx.user_message,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ctx.user_message},
        ]

        result = await self.call_llm_json(messages, temperature=0.5)
        if not result.get("resource_bundle"):
            bundle = []
            for item in result.get("resources", [])[:5]:
                bundle.append({
                    "topic": item.get("topic", ""),
                    "recommended_types": [item.get("type", "lecture")],
                    "why": item.get("reason", ""),
                })
            result["resource_bundle"] = bundle

        stream.result(result)
        stream.stage_end("resource_plan")
        return result


from config import settings
