from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


class GeneratorAgent(BaseAgent):
    """内容生成 Agent — 生成个性化学习资源。
    
    支持生成：讲义、练习题、代码案例、思维导图描述。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="generator_agent", module_name="generator")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        resource_type = ctx.config_overrides.get("resource_type", "lecture")
        stream.stage_start("generate", f"正在生成{resource_type}...")

        from services.profile_service import profile_service
        from services.mastery_service import mastery_service
        from services.rag_service import rag_service

        profile = profile_service.get_profile(ctx.user_id)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        topic = ctx.config_overrides.get("topic", "")

        rag_context = rag_service.get_context_for_topic(topic or ctx.user_message)

        previous_questions = ""
        if resource_type == "quiz":
            from services.resource_service import resource_service
            existing_quizzes = resource_service.get_resources(ctx.user_id, "quiz")
            if existing_quizzes:
                recent = existing_quizzes[0].get("content", "")[:500]
                previous_questions = recent

        prompt = self.load_prompt(f"generate_{resource_type}", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "mastery": json.dumps(mastery, ensure_ascii=False, indent=2),
            "user_message": ctx.user_message,
            "topic": topic,
            "previous_questions": previous_questions,
        })

        messages = [{"role": "system", "content": prompt}]
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"以下是与该主题相关的课程知识库内容，请参考这些内容来生成准确的资源：\n\n{rag_context}",
            })
        messages.append({"role": "user", "content": ctx.user_message})

        full_response = ""
        async for chunk in self.stream_llm(messages, temperature=0.7, max_tokens=3000):
            full_response += chunk
            stream.content(chunk)

        safety_result = None
        try:
            from agents.safety import SafetyAgent
            safety = SafetyAgent()
            safety_result = await safety.review_content(full_response, resource_type)
            if safety_result and not safety_result.get("is_safe", True):
                issues = safety_result.get("issues", [])
                stream.thinking(f"安全审查发现 {len(issues)} 个问题")
        except Exception:
            pass

        from services.resource_service import resource_service
        safety_extra = {}
        if safety_result:
            safety_extra = {
                "safety_checked": True,
                "safety_issues": safety_result.get("issues", []),
                "safety_suggestions": safety_result.get("suggestions", []),
                "is_safe": safety_result.get("is_safe", True),
            }
        saved = resource_service.save_resource(
            ctx.user_id,
            ctx.config_overrides.get("topic", ""),
            resource_type,
            full_response,
            **safety_extra,
        )

        result = {
            "resource_type": resource_type,
            "content": full_response,
            "resource_id": saved.get("id", ""),
            "safety": safety_result,
        }
        stream.result(result)
        stream.stage_end("generate")
        return result

    async def generate_lecture(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "lecture"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的个性化讲义"
        return await self.process(ctx, stream)

    async def generate_quiz(self, topic: str, num_questions: int, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "quiz"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成{num_questions}道关于「{topic}」的分层练习题"
        return await self.process(ctx, stream)

    async def generate_code_example(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "code"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的代码实操案例"
        return await self.process(ctx, stream)

    async def generate_mindmap(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "mindmap"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的知识点思维导图（用 Markdown 缩进列表表示）"
        return await self.process(ctx, stream)
