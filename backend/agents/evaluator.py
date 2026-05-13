from __future__ import annotations

import json
import re
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
        from agents.diagnostic import DiagnosticAgent
        from services.resource_service import resource_service

        mastery_updates = []
        judged_results = []
        for qr in quiz_results:
            topic_id = qr.get("topic_id", "general")
            judged = self._judge_quiz_result(qr)
            correct = judged["correct"]
            difficulty = qr.get("difficulty", 0.5)

            update = mastery_service.update_mastery(ctx.user_id, topic_id, correct, difficulty)
            mastery_updates.append(update)
            judged_results.append({**qr, **judged})

        weak_topics = mastery_service.get_weak_topics(ctx.user_id)
        summary = mastery_service.get_mastery_summary(ctx.user_id)
        recent_events = resource_service.get_events(ctx.user_id)[:20]

        diagnostic = DiagnosticAgent()
        diagnosis = await diagnostic.diagnose_from_quiz(judged_results, ctx.user_id)

        recommendations = []
        if weak_topics:
            recommendations.append({
                "type": "review",
                "topics": [t["topic_id"] for t in weak_topics[:3]],
                "message": f"建议重点复习：{', '.join(t['topic_id'] for t in weak_topics[:3])}",
            })

        mistake_pattern = self._build_mistake_pattern(judged_results)
        resource_recommendations = self._build_resource_recommendations(weak_topics, recent_events)
        path_adjustment_reason = self._build_path_adjustment_reason(judged_results, weak_topics)

        result = {
            "mastery_updates": mastery_updates,
            "mastery_summary": summary,
            "weak_topics": weak_topics,
            "weak_topics_ranked": weak_topics[:5],
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "mistake_pattern": mistake_pattern,
            "resource_recommendations": resource_recommendations,
            "path_adjustment_reason": path_adjustment_reason,
            "judged_results": judged_results,
            "accuracy": sum(1 for r in judged_results if r.get("correct")) / max(len(judged_results), 1),
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

    def _judge_quiz_result(self, result: dict[str, Any]) -> dict[str, Any]:
        question_type = result.get("question_type") or result.get("type") or "choice"
        student_answer = (result.get("student_answer") or "").strip()
        correct_answer = str(result.get("correct_answer") or result.get("answer") or "").strip()

        if question_type == "fill":
            normalized_student = re.sub(r"\s+", "", student_answer).lower()
            normalized_answer = re.sub(r"\s+", "", correct_answer).lower()
            correct = normalized_student == normalized_answer and normalized_answer != ""
            return {
                "correct": correct,
                "judge_reason": "答案归一化匹配" if correct else f"标准答案为 {correct_answer}",
                "judge_score": 1.0 if correct else 0.0,
            }

        if question_type == "code":
            required_keywords = [kw.lower() for kw in result.get("required_keywords", []) if kw]
            expected_points = result.get("expected_points", [])
            test_cases = result.get("test_cases", [])

            keyword_hits = sum(1 for kw in required_keywords if kw in student_answer.lower())
            keyword_score = keyword_hits / max(len(required_keywords), 1) if required_keywords else 0.0

            point_hits = sum(1 for point in expected_points if str(point).lower() in student_answer.lower())
            point_score = point_hits / max(len(expected_points), 1) if expected_points else 0.0

            testcase_score = 0.0
            if test_cases:
                testcase_score = min(0.4, 0.2 * len(test_cases))

            total_score = round(min(1.0, keyword_score * 0.5 + point_score * 0.3 + testcase_score), 2)
            correct = total_score >= 0.6 and len(student_answer) >= 20

            return {
                "correct": correct,
                "judge_reason": f"关键字命中 {keyword_hits}/{len(required_keywords) or 0}，要点命中 {point_hits}/{len(expected_points) or 0}",
                "judge_score": total_score,
            }

        correct = student_answer == correct_answer and correct_answer != ""
        return {
            "correct": correct,
            "judge_reason": "选项匹配" if correct else f"正确答案为 {correct_answer}",
            "judge_score": 1.0 if correct else 0.0,
        }

    def _build_mistake_pattern(self, judged_results: list[dict[str, Any]]) -> dict[str, Any]:
        wrong = [r for r in judged_results if not r.get("correct")]
        by_type: dict[str, int] = {}
        by_topic: dict[str, int] = {}
        for item in wrong:
            by_type[item.get("question_type") or item.get("type") or "choice"] = by_type.get(item.get("question_type") or item.get("type") or "choice", 0) + 1
            topic = item.get("topic_id", "general")
            by_topic[topic] = by_topic.get(topic, 0) + 1
        return {
            "wrong_count": len(wrong),
            "by_type": by_type,
            "by_topic": by_topic,
        }

    def _build_resource_recommendations(self, weak_topics: list[dict], recent_events: list[dict]) -> list[dict]:
        viewed_ids = {event.get("resource_id") for event in recent_events if event.get("event_type") == "open"}
        recommendations = []
        for topic in weak_topics[:3]:
            recommendations.append({
                "topic": topic["topic_id"],
                "recommended_types": ["lecture", "ppt_outline", "quiz", "code_lab"],
                "reason": f"{topic['topic_id']} 当前掌握度 {topic['level']:.0%}，需要讲解+练习+实操组合补强",
                "recently_viewed_resource_ids": list(viewed_ids)[:5],
            })
        return recommendations

    def _build_path_adjustment_reason(self, judged_results: list[dict], weak_topics: list[dict]) -> str:
        if not judged_results:
            return "暂无新的练习结果，本次路径保持不变。"
        wrong_topics = [item.get("topic_id", "general") for item in judged_results if not item.get("correct")]
        if wrong_topics:
            focus = ", ".join(dict.fromkeys(wrong_topics))
            return f"由于最近练习在 {focus} 上错误较多，这些知识点应前移复习，并补充讲义、PPT 和练习资源。"
        if weak_topics:
            return "整体正确率较好，但仍存在薄弱点，建议保留当前路径顺序并对薄弱知识点追加补强资源。"
        return "最近练习表现稳定，可维持当前路径并逐步推进后续知识点。"
