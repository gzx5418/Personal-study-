# -*- coding: utf-8 -*-
"""资源生成子 Agent 的公共基类。"""
from __future__ import annotations

import json
import logging
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus

logger = logging.getLogger(__name__)


class ResourceSubAgent(BaseAgent):
    """资源子 Agent 基类。

    子类只需设置:
      - _resource_type: 资源类型键名 (如 "lecture", "quiz")
      - _display_name: 中文显示名 (如 "讲义生成")
      - _prompt_key:    prompt 模板键名 (如 "generate_lecture")
    """

    _resource_type: str = ""
    _display_name: str = ""
    _prompt_key: str = ""
    _user_msg_template: str = "请为我生成关于「{topic}」的{display}"

    def __init__(self, agent_name: str, capability: str) -> None:
        super().__init__(agent_name=agent_name, module_name="generator")
        self._capability = capability

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start(self._capability, f"{self._display_name}智能体正在工作...")

        requested_type = ctx.config_overrides.get("resource_type", self._resource_type)
        topic = ctx.config_overrides.get("topic", "")
        course_id = ctx.config_overrides.get("course_id") or ctx.metadata.get("course_id", "")

        # --- 检索画像、掌握度、RAG ---
        from services.profile_service import profile_service
        from services.mastery_service import mastery_service
        from services.rag_service import rag_service

        profile = profile_service.get_profile(ctx.user_id)
        mastery = mastery_service.get_user_mastery(ctx.user_id)

        rag_result = rag_service.get_context_for_topic(topic or ctx.user_message, kb_name=course_id)
        rag_context = rag_result.get("context", "")
        rag_sources = rag_result.get("sources", [])

        from services.confidence_service import confidence_service
        confidence_info = confidence_service.calculate_confidence(
            topic or ctx.user_message, rag_sources,
        )
        confidence = confidence_info["score"]
        logger.info("[%s] RAG confidence=%d topic=%s", self._capability, confidence, topic)

        previous_questions = ""
        if self._resource_type == "quiz":
            from services.resource_service import resource_service
            existing = resource_service.get_resources(ctx.user_id, "quiz")
            if existing:
                previous_questions = existing[0].get("content", "")[:500]

        # --- 构造 prompt ---
        prompt = self.load_prompt(self._prompt_key, {
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
                "resource_type": self._resource_type,
                "content": fallback,
                "resource_id": "",
                "agent_name": self._capability,
                "safety": {"is_safe": True, "issues": [], "suggestions": ["补充更具体的课程范围或上传资料"]},
                "sources_used": [],
                "degraded": True,
                "confidence": 0,
                "confidence_breakdown": confidence_info.get("breakdown", {}),
            }
            stream.result(result)
            stream.stage_end(self._capability)
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
        if confidence < 30:
            warning = (
                f"⚠️ 置信度较低（{confidence}/100）：当前知识库中关于「{topic or ctx.user_message}」"
                "的检索结果有限，以下内容可能不够准确，请结合教材和教师指导进行判断。\n\n"
            )
            full_response += warning
            stream.content(warning)
            stream.thinking(f"置信度过低: {confidence}/100，已添加低置信度警告")

        async for chunk in self.stream_llm(messages, temperature=0.7, max_tokens=3000):
            full_response += chunk
            stream.content(chunk)

        # 参考来源
        if rag_sources:
            citations = "\n\n---\n\n## 参考来源\n\n"
            for idx, src in enumerate(rag_sources, 1):
                title = src.get("title", "未知")
                chapter = src.get("chapter", "")
                source_id = src.get("source_id", "")
                cid = src.get("course_id", "")
                ch = f" - {chapter}" if chapter else ""
                citations += f"{idx}. **{title}**{ch}（{cid}::{source_id}）\n"
            full_response += citations
            stream.content(citations)

        # 安全审查
        safety_result = None
        try:
            from agents.safety import SafetyAgent
            safety = SafetyAgent()
            safety_result = await safety.review_content(full_response, self._resource_type, rag_sources)
            if safety_result and not safety_result.get("is_safe", True):
                issues = safety_result.get("issues", [])
                stream.thinking(f"[{self._capability}] 安全审查发现 {len(issues)} 个问题")
        except Exception as exc:
            logger.warning("[%s] Safety review skipped: %s", self._capability, exc)
            safety_result = {
                "is_safe": None, "review_skipped": True, "issues": [],
                "suggestions": ["安全审查未完成，请结合内容依据人工复核。"],
            }
            stream.thinking(f"[{self._capability}] 安全审查未完成")

        # 保存
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
            ctx.user_id, topic, self._resource_type, full_response,
            course_id=course_id, sources_used=rag_sources,
            resource_meta={"agent_name": self._capability, "topic": topic, "course_id": course_id},
            **safety_extra,
        )

        result = {
            "resource_type": self._resource_type,
            "content": full_response,
            "resource_id": saved.get("id", ""),
            "agent_name": self._capability,
            "safety": safety_result,
            "sources_used": rag_sources,
            "confidence": confidence,
            "confidence_breakdown": confidence_info.get("breakdown", {}),
        }
        stream.result(result)
        stream.stage_end(self._capability)
        return result
