from __future__ import annotations

import asyncio
import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus
from config import settings


class ChatAgent(BaseAgent):
    """通用对话 Agent，支持 RAG 增强的多轮对话。"""

    def __init__(self) -> None:
        super().__init__(agent_name="chat_agent", module_name="chat")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("chat", "正在思考...")

        profile_text = ctx.profile_context.get("text", "")
        mastery_text = ctx.mastery_context.get("text", "")

        system_prompt = self.load_prompt("system", {
            "profile": profile_text or "暂无画像信息",
            "mastery": mastery_text or "暂无掌握度信息",
        })

        rag_context = ""
        kb_refs = ctx.knowledge_base_refs or [settings.COURSE_ID]
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
            vl_model = "zai-org/GLM-4.6V"
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
        session_service.add_message(ctx.session_id, "user", ctx.user_message)
        session_service.add_message(ctx.session_id, "assistant", full_response)

        asyncio.create_task(session_service.auto_refresh_memory(ctx.session_id, ctx.user_id))

        stream.stage_end("chat")
        return {"response": full_response}
