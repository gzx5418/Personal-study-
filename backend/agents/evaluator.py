from __future__ import annotations

import json
import time
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


class EvaluatorAgent(BaseAgent):
    """评估反馈 Agent — 项目核心创新点之一。
    
    评估学习效果，更新掌握度，触发路径调整。
    形成"做题→评估→调路径→推资源"闭环。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="evaluator_agent", module_name="evaluator")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("evaluate", "正在评估学习效果...")

        quiz_data = ctx.config_overrides.get("quiz_results", [])
        if quiz_data:
            result = await self._evaluate_quiz(ctx, quiz_data, stream)
        else:
            result = await self._evaluate_conversation(ctx, stream)

        stream.result(result)
        stream.stage_end("evaluate")
        return result

    async def _evaluate_quiz(self, ctx: UnifiedContext, quiz_results: list[dict], stream: StreamBus) -> dict:
        from services.mastery_service import mastery_service
        from services.profile_service import profile_service
        from agents.diagnostic import DiagnosticAgent

        mastery_updates = []
        for qr in quiz_results:
            topic_id = qr.get("topic_id", "general")
            correct = qr.get("correct", False)
            difficulty = qr.get("difficulty", 0.5)

            update = mastery_service.update_mastery(ctx.user_id, topic_id, correct, difficulty)
            mastery_updates.append(update)

        weak_topics = mastery_service.get_weak_topics(ctx.user_id)
        summary = mastery_service.get_mastery_summary(ctx.user_id)

        diagnostic = DiagnosticAgent()
        diagnosis = await diagnostic.diagnose_from_quiz(quiz_results, ctx.user_id)

        recommendations = []
        if weak_topics:
            recommendations.append({
                "type": "review",
                "topics": [t["topic_id"] for t in weak_topics[:3]],
                "message": f"建议重点复习：{', '.join(t['topic_id'] for t in weak_topics[:3])}",
            })

        result = {
            "mastery_updates": mastery_updates,
            "mastery_summary": summary,
            "weak_topics": weak_topics,
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "accuracy": sum(1 for r in quiz_results if r.get("correct")) / max(len(quiz_results), 1),
        }

        stream.thinking(f"评估完成，正确率 {result['accuracy']:.0%}，{len(weak_topics)} 个薄弱知识点")
        return result

    async def _evaluate_conversation(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        from services.profile_service import profile_service

        profile = profile_service.get_profile(ctx.user_id)
        history = ctx.history[-6:]

        prompt = self.load_prompt("evaluate_conversation", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "conversation": json.dumps(history, ensure_ascii=False, indent=2),
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请评估这段对话中的学习效果。"},
        ]

        result = await self.call_llm_json(messages, temperature=0.3)
        return result

    async def submit_quiz_results(self, user_id: str, session_id: str, quiz_results: list[dict]) -> dict:
        """提交练习结果，更新掌握度并返回评估报告。"""
        from services.mastery_service import mastery_service

        updates = []
        for qr in quiz_results:
            update = mastery_service.update_mastery(
                user_id=user_id,
                topic_id=qr.get("topic_id", "general"),
                correct=qr.get("correct", False),
                difficulty=qr.get("difficulty", 0.5),
            )
            updates.append(update)

        return {
            "updates": updates,
            "summary": mastery_service.get_mastery_summary(user_id),
            "weak_topics": mastery_service.get_weak_topics(user_id),
        }
