from __future__ import annotations

import json
import logging
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
        self._resource_aliases = {
            "code": "code_lab",
            "code_lab": "code_lab",
            "ppt": "ppt_outline",
            "ppt_outline": "ppt_outline",
            "reading": "extended_reading",
            "extended_reading": "extended_reading",
            "lecture": "lecture",
            "quiz": "quiz",
            "mindmap": "mindmap",
            "animation": "animation",
            "video": "animation",
        }

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        requested_type = ctx.config_overrides.get("resource_type", "lecture")
        resource_type = self._resource_aliases.get(requested_type, requested_type)
        stream.stage_start("generate", f"正在生成{resource_type}...")

        from services.profile_service import profile_service
        from services.mastery_service import mastery_service
        from services.rag_service import rag_service

        profile = profile_service.get_profile(ctx.user_id)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        topic = ctx.config_overrides.get("topic", "")
        course_id = ctx.config_overrides.get("course_id") or ctx.metadata.get("course_id", "")

        rag_result = rag_service.get_context_for_topic(topic or ctx.user_message, kb_name=course_id)
        rag_context = rag_result.get("context", "")
        rag_sources = rag_result.get("sources", [])

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
            "course_id": course_id,
            "sources": json.dumps(rag_sources, ensure_ascii=False, indent=2),
        })

        if not rag_context:
            fallback = (
                f"当前知识库中没有检索到足够的《{topic or ctx.user_message}》课程依据。\n\n"
                "为保证内容准确性，我暂时不直接生成完整学习资源。建议你：\n"
                "1. 进一步缩小主题范围\n"
                "2. 上传相关课程资料\n"
                "3. 切换到已有课程知识点后再生成"
            )
            stream.content(fallback)
            result = {
                "resource_type": resource_type,
                "content": fallback,
                "resource_id": "",
                "safety": {"is_safe": True, "issues": [], "suggestions": ["补充更具体的课程范围或上传资料"]},
                "sources_used": [],
                "degraded": True,
            }
            stream.result(result)
            stream.stage_end("generate")
            return result

        messages = [{"role": "system", "content": prompt}]
        messages.append({
            "role": "system",
            "content": (
                "你必须严格基于给定课程知识库来源生成内容。"
                "输出内容时，最后追加一个 `## 内容依据` 小节，列出使用到的 source_id、章节和标题。"
                "如果某部分无法从来源中得到支持，必须明确说明而不是自行补充。"
            ),
        })
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
            safety_result = await safety.review_content(full_response, resource_type, rag_sources)
            if safety_result and not safety_result.get("is_safe", True):
                issues = safety_result.get("issues", [])
                stream.thinking(f"安全审查发现 {len(issues)} 个问题")
        except Exception as exc:
            logging.getLogger(__name__).warning("Safety review skipped: %s", exc)
            safety_result = {
                "is_safe": None,
                "review_skipped": True,
                "issues": [],
                "suggestions": ["安全审查未完成，请结合内容依据人工复核。"],
            }
            stream.thinking("安全审查未完成，已保留内容依据供人工复核")

        from services.resource_service import resource_service
        safety_extra = {}
        if safety_result:
            safety_extra = {
                "safety_checked": not safety_result.get("review_skipped", False),
                "safety_issues": safety_result.get("issues", []),
                "safety_suggestions": safety_result.get("suggestions", []),
                "is_safe": safety_result.get("is_safe") is not False,
            }
        saved = resource_service.save_resource(
            ctx.user_id,
            ctx.config_overrides.get("topic", ""),
            resource_type,
            full_response,
            course_id=course_id,
            sources_used=rag_sources,
            resource_meta={"requested_type": requested_type, "topic": topic, "course_id": course_id},
            **safety_extra,
        )

        result = {
            "resource_type": resource_type,
            "content": full_response,
            "resource_id": saved.get("id", ""),
            "safety": safety_result,
            "sources_used": rag_sources,
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
        ctx.config_overrides["resource_type"] = "code_lab"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的代码实操案例"
        return await self.process(ctx, stream)

    async def generate_mindmap(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "mindmap"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的知识点思维导图（用 Markdown 缩进列表表示）"
        return await self.process(ctx, stream)

    async def generate_ppt_outline(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "ppt_outline"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的教学PPT提纲"
        return await self.process(ctx, stream)

    async def generate_extended_reading(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "extended_reading"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的拓展阅读材料"
        return await self.process(ctx, stream)

    async def generate_animation(self, topic: str, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.config_overrides["resource_type"] = "animation"
        ctx.config_overrides["topic"] = topic
        ctx.user_message = f"请为我生成关于「{topic}」的教学动画脚本和可视化分镜"
        return await self.process(ctx, stream)
