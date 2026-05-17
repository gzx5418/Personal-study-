from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus
from config import settings

logger = logging.getLogger(__name__)


@register_agent("chat")
class ChatAgent(BaseAgent):
    """通用对话 Agent，支持 RAG 增强的多轮对话。"""

    def __init__(self) -> None:
        super().__init__(agent_name="chat_agent", module_name="chat")

    async def _load_historical_context(self, user_id: str) -> str:
        from services.session_service import session_service

        context_parts = []

        try:
            sessions = session_service.list_sessions(user_id)
            if sessions:
                recent_session = sessions[-1].get("session_id", "")
                if recent_session:
                    summary = await session_service.generate_session_summary(recent_session, user_id)
                    if summary:
                        context_parts.append(f"【上次对话摘要】\n{summary}")
        except Exception as e:
            logger.warning("加载会话摘要失败: %s", str(e))

        try:
            progress = session_service.get_learning_progress(user_id)
            if progress.get("session_count", 0) > 0:
                topics = progress.get("topics_covered", [])
                topics_str = "、".join(topics[:5]) if topics else "暂无"
                context_parts.append(
                    f"【学习进度】已进行 {progress['session_count']} 次会话，"
                    f"共 {progress['total_messages']} 条消息，"
                    f"覆盖知识点：{topics_str}"
                )
        except Exception as e:
            logger.warning("加载学习进度失败: %s", str(e))

        try:
            from services.profile_service import profile_service
            profile = profile_service.get_profile(user_id)
            weak_points = profile.get("weak_points", [])
            if weak_points:
                weak_str = "、".join(weak_points[:3])
                context_parts.append(f"【薄弱知识点】{weak_str}")
        except Exception as e:
            logger.warning("加载薄弱知识点失败: %s", str(e))

        historical_context = "\n\n".join(context_parts)
        logger.debug("加载历史上下文: user=%s, length=%d", user_id, len(historical_context))
        return historical_context

    async def _update_learning_state(self, ctx: UnifiedContext, response: str) -> None:
        from services.session_service import session_service

        try:
            user_message = ctx.user_message
            if len(user_message) < 10:
                return

            topic_indicators = ["什么是", "如何", "怎么", "为什么", "请解释", "帮我", "告诉我", "介绍一下"]
            is_learning_topic = any(indicator in user_message for indicator in topic_indicators)

            if not is_learning_topic:
                return

            prompt = f"""请分析以下对话，提取讨论的知识点。

用户问题：{user_message}
助手回答：{response[:500]}

请返回一个JSON格式：
{{"topics": ["知识点1", "知识点2"], "understanding": "good/average/poor"}}

只返回JSON，不要其他内容。"""

            messages = [{"role": "user", "content": prompt}]
            from services.llm_service import llm_service
            result_text = await llm_service.chat(messages=messages, temperature=0.2, max_tokens=200)

            try:
                result = json.loads(result_text)
                topics = result.get("topics", [])
                understanding = result.get("understanding", "average")

                if topics:
                    session_service.add_message(
                        ctx.session_id,
                        "system",
                        f"[知识点提取] {', '.join(topics)} - 理解程度: {understanding}",
                        user_id=ctx.user_id
                    )
                    logger.info("更新学习状态: user=%s, topics=%s", ctx.user_id, topics)
            except json.JSONDecodeError:
                logger.debug("知识点提取结果解析失败")

        except Exception as e:
            logger.warning("更新学习状态失败: %s", str(e))

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("chat", "正在思考...")

        historical_context = await self._load_historical_context(ctx.user_id)

        profile_text = ctx.profile_context.get("text", "")
        mastery_text = ctx.mastery_context.get("text", "")

        system_prompt = self.load_prompt("system", {
            "profile": profile_text or "暂无画像信息",
            "mastery": mastery_text or "暂无掌握度信息",
        })

        if historical_context:
            system_prompt = f"{system_prompt}\n\n以下是学生的历史学习上下文，请参考：\n\n{historical_context}"

        rag_context = ""
        course_id = ctx.metadata.get("course_id", settings.COURSE_ID)
        kb_refs = ctx.knowledge_base_refs or [course_id]
        if kb_refs:
            from services.rag_service import rag_service
            for kb in kb_refs:
                result = await rag_service.search(ctx.user_message, kb_name=kb)
                if result.get("sources"):
                    rag_context = result["answer"]
                    stream.sources(result["sources"])
                    break

        messages = [{"role": "system", "content": system_prompt}]
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"以下是从知识库中检索到的相关内容，请参考回答：\n\n{rag_context}",
            })
        messages.extend(ctx.history[-settings.MAX_HISTORY_TURNS:])

        image_base64 = ctx.config_overrides.get("image_base64", "")
        file_content = ctx.config_overrides.get("file_content", "")
        file_name = ctx.config_overrides.get("file_name", "")

        if image_base64:
            user_content = [
                {"type": "text", "text": ctx.user_message},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
            ]
            messages.append({"role": "user", "content": user_content})
            vl_model = ctx.config_overrides.get("vision_model") or settings.LLM_VISION_MODEL
            full_response = ""
            async for chunk in self.stream_llm(messages, temperature=0.7, model=vl_model):
                full_response += chunk
                stream.content(chunk)
        elif file_content:
            ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            lang_map = {"py": "python", "js": "javascript", "java": "java", "cpp": "cpp", "c": "c", "h": "c", "html": "html", "css": "css", "json": "json", "sql": "sql", "sh": "bash", "txt": "text", "md": "markdown", "csv": "csv", "yaml": "yaml", "yml": "yaml"}
            lang = lang_map.get(ext, "text")
            file_msg = f"{ctx.user_message}\n\n[上传文件: {file_name}]\n```{lang}\n{file_content}\n```"
            messages.append({"role": "user", "content": file_msg})
            full_response = ""
            async for chunk in self.stream_llm(messages, temperature=0.7):
                full_response += chunk
                stream.content(chunk)
        else:
            messages.append({"role": "user", "content": ctx.user_message})
            full_response = ""
            async for chunk in self.stream_llm(messages, temperature=0.7):
                full_response += chunk
                stream.content(chunk)

        full_response = full_response.replace("<|begin_of_box|>", "").replace("<|end_of_box|>", "").strip()

        from services.session_service import session_service

        async def _safe_refresh():
            try:
                await session_service.auto_refresh_memory(ctx.session_id, ctx.user_id)
            except Exception as e:
                logger.warning("auto_refresh_memory failed: %s", str(e))

        async def _safe_update():
            try:
                await self._update_learning_state(ctx, full_response)
            except Exception as e:
                logger.warning("_update_learning_state failed: %s", str(e))

        asyncio.create_task(_safe_refresh())
        asyncio.create_task(_safe_update())

        stream.stage_end("chat")
        return {"response": full_response}
