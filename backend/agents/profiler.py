from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


@register_agent("profile")
class ProfilerAgent(BaseAgent):
    """学生画像 Agent — 对话驱动的无感画像构建。
    
    从对话中自动提取学生信息，更新结构化画像。
    这是项目的四大创新点之一：对话驱动的无感画像构建。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="profiler_agent", module_name="profile")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("profile", "正在分析学习画像...")

        from services.profile_service import profile_service
        current_profile = profile_service.get_profile(ctx.user_id)

        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in ctx.history[-10:]
        )

        prompt = self.load_prompt("extract", {
            "current_profile": json.dumps(current_profile, ensure_ascii=False, indent=2),
            "conversation": history_text,
            "user_message": ctx.user_message,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请根据以上对话分析学生画像，当前画像：{json.dumps(current_profile, ensure_ascii=False)}"},
        ]

        result = await self.call_llm_json(messages, temperature=0.3)

        if result.get("should_update") and result.get("updates"):
            updated = profile_service.update_profile(ctx.user_id, result["updates"])
            stream.content(f"画像已更新：{json.dumps(result['updates'], ensure_ascii=False)}")
            stream.result({"profile": updated, "updated": True})
            return {"profile": updated, "updated": True}
        else:
            stream.content("画像无需更新")
            stream.result({"profile": current_profile, "updated": False})
            return {"profile": current_profile, "updated": False}

    async def extract_from_conversation(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        """从对话中提取画像信息（用于对话结束后的异步更新）。"""
        return await self.process(ctx, stream)
