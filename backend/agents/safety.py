from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


class SafetyAgent(BaseAgent):
    """安全审查 Agent — 对生成内容进行质量校验。
    
    检查生成内容是否存在：
    - 事实性错误（与知识库矛盾）
    - 不当内容
    - 格式问题
    """

    def __init__(self) -> None:
        super().__init__(agent_name="safety_agent", module_name="safety")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("safety", "正在审查内容...")

        content = ctx.config_overrides.get("content_to_review", "")
        content_type = ctx.config_overrides.get("content_type", "general")

        prompt = self.load_prompt("review", {
            "content": content,
            "content_type": content_type,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请审查以上内容的质量和准确性。"},
        ]

        result = await self.call_llm_json(messages, temperature=0.2)

        is_safe = result.get("is_safe", True)
        issues = result.get("issues", [])

        if not is_safe:
            stream.thinking(f"发现 {len(issues)} 个问题")

        stream.result({"is_safe": is_safe, "issues": issues, "suggestions": result.get("suggestions", [])})
        stream.stage_end("safety")
        return result

    async def review_content(self, content: str, content_type: str = "general") -> dict:
        """直接审查内容（供其他 Agent 调用）。"""
        ctx = UnifiedContext()
        ctx.config_overrides = {"content_to_review": content, "content_type": content_type}
        stream = StreamBus()
        return await self.process(ctx, stream)
