from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


class DiagnosticAgent(BaseAgent):
    """学习诊断 Agent — 项目核心创新点之一。
    
    分析学生的错题模式、对话中的困惑信号，输出结构化诊断报告。
    DeepTutor 没有此模块，完全自建。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="diagnostic_agent", module_name="diagnostic")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("diagnostic", "正在诊断学习情况...")

        from services.mastery_service import mastery_service
        from services.profile_service import profile_service

        mastery = mastery_service.get_user_mastery(ctx.user_id)
        profile = profile_service.get_profile(ctx.user_id)
        weak_topics = mastery_service.get_weak_topics(ctx.user_id)

        prompt = self.load_prompt("diagnose", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "mastery": json.dumps(mastery, ensure_ascii=False, indent=2),
            "weak_topics": json.dumps(weak_topics, ensure_ascii=False, indent=2),
            "user_message": ctx.user_message,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ctx.user_message},
        ]

        result = await self.call_llm_json(messages, temperature=0.3)

        stream.thinking(json.dumps(result.get("analysis", {}), ensure_ascii=False))
        stream.result(result)
        stream.stage_end("diagnostic")

        return result

    async def diagnose_from_quiz(self, quiz_results: list[dict], user_id: str) -> dict:
        """从练习结果中诊断薄弱点。"""
        from services.mastery_service import mastery_service

        error_patterns = []
        for r in quiz_results:
            if not r.get("correct"):
                error_patterns.append({
                    "topic": r.get("topic_id"),
                    "question": r.get("question", ""),
                    "student_answer": r.get("student_answer", ""),
                    "correct_answer": r.get("correct_answer", ""),
                    "error_type": r.get("error_type", "unknown"),
                })

        prompt = self.load_prompt("quiz_diagnose", {
            "error_patterns": json.dumps(error_patterns, ensure_ascii=False, indent=2),
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请分析以上错题模式，诊断学习薄弱点。"},
        ]

        result = await self.call_llm_json(messages, temperature=0.3)
        return result
