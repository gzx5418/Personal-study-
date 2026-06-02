from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from core.context import UnifiedContext
from core.orchestrator import orchestrator
from core.stream_bus import StreamBus
from config import settings

logger = logging.getLogger("zhixue.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000)
    session_id: str = Field(default="default", max_length=64)
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    capability: str = Field(default="chat", max_length=32)
    knowledge_bases: list[str] = Field(default_factory=list, max_length=32)
    image_base64: str = Field(default="", max_length=30_000_000)
    file_content: str = Field(default="", max_length=2_000_000)
    file_name: str = Field(default="", max_length=255)
    course_id: str = Field(default=settings.COURSE_ID, max_length=64)
    llm_model: str = Field(default="", max_length=128)
    reasoning_model: str = Field(default="", max_length=128)
    vision_model: str = Field(default="", max_length=128)
    embedding_model: str = Field(default="", max_length=128)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: list[dict] = Field(default_factory=list)


def _build_chat_context(
    req: ChatRequest,
    history: list,
    user_msg: str | None = None,
) -> UnifiedContext:
    """构建统一的聊天上下文（chat 与 chat_sync 共享）。"""
    from services.profile_service import profile_service
    from services.mastery_service import mastery_service

    mastery_summary = mastery_service.get_mastery_summary(req.user_id)
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id or settings.DEFAULT_USER_ID,
        user_message=user_msg if user_msg is not None else req.message,
        active_capability=req.capability,
        history=history,
        knowledge_base_refs=req.knowledge_bases,
        profile_context={"text": profile_service.get_profile_context_text(req.user_id)},
        mastery_context={"text": json.dumps(mastery_summary, ensure_ascii=False)},
        metadata={"course_id": req.course_id},
    )
    if req.image_base64:
        ctx.config_overrides["image_base64"] = req.image_base64
    if req.file_content:
        ctx.config_overrides["file_content"] = req.file_content
        ctx.config_overrides["file_name"] = req.file_name
    if req.llm_model:
        ctx.config_overrides["llm_model"] = req.llm_model
    if req.reasoning_model:
        ctx.config_overrides["reasoning_model"] = req.reasoning_model
    if req.vision_model:
        ctx.config_overrides["vision_model"] = req.vision_model
    if req.embedding_model:
        ctx.config_overrides["embedding_model"] = req.embedding_model
    return ctx


@router.post("")
async def chat(req: ChatRequest) -> StreamingResponse:
    from services.session_service import session_service

    image_url = ""
    if req.image_base64:
        import base64, os, uuid
        img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
        os.makedirs(img_dir, exist_ok=True)
        filename = f"img_{uuid.uuid4().hex}.png"
        filepath = os.path.join(img_dir, filename)
        try:
            img_data = base64.b64decode(req.image_base64)
            with open(filepath, "wb") as f:
                f.write(img_data)
            image_url = f"/api/chat/image/{filename}"
        except Exception as e:
            logger.warning(f"图片保存失败: {e}")

    user_msg = req.message
    if image_url:
        user_msg = f"{user_msg}\n[用户上传了一张图片: {image_url}]" if user_msg else f"[用户上传了一张图片: {image_url}]"

    await run_in_threadpool(session_service.add_message, req.session_id, "user", user_msg, user_id=req.user_id)

    history = await run_in_threadpool(session_service.get_history, req.session_id, user_id=req.user_id)

    ctx = await run_in_threadpool(_build_chat_context, req, history, user_msg)

    stream = await orchestrator.dispatch(ctx)

    async def event_generator() -> AsyncIterator[str]:
        collected = []
        async for event in stream.subscribe():
            yield event.to_sse()
            if event.type.value == "content":
                collected.append(event.data.get("text", ""))

        full_response = "".join(collected)
        if full_response:
            await run_in_threadpool(session_service.add_message, req.session_id, "assistant", full_response, user_id=req.user_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sync")
async def chat_sync(req: ChatRequest) -> ChatResponse:
    from services.session_service import session_service

    await run_in_threadpool(session_service.add_message, req.session_id, "user", req.message, user_id=req.user_id)

    history = await run_in_threadpool(session_service.get_history, req.session_id, user_id=req.user_id)

    ctx = await run_in_threadpool(_build_chat_context, req, history)

    result = await orchestrator.dispatch_sync(ctx)
    if not result.get("success", True):
        response = f"Error: {result.get('error', 'Unknown error')}"
    else:
        response = result.get("response", "") or result.get("question", "")
    if response:
        await run_in_threadpool(session_service.add_message, req.session_id, "assistant", response, user_id=req.user_id)

    return ChatResponse(
        session_id=req.session_id,
        response=response,
        sources=result.get("sources", []),
    )


@router.get("/sessions/{user_id}")
def list_sessions(user_id: str):
    from services.session_service import session_service
    sessions = session_service.list_sessions(user_id)
    result = []
    for s in sessions:
        sid = s["session_id"]
        history = session_service.get_history(sid)
        first_msg = ""
        last_msg = ""
        msg_count = len(history)
        for m in history:
            if m["role"] == "user" and not first_msg:
                first_msg = m["content"][:50]
            if m["role"] == "assistant":
                last_msg = m["content"][:80]
        if first_msg or msg_count > 0:
            result.append({
                "session_id": sid,
                "first_message": first_msg,
                "last_message": last_msg,
                "message_count": msg_count,
            })
    return {"sessions": result}


@router.delete("/session/{session_id}")
def delete_session(session_id: str, user_id: str = Query(default=settings.DEFAULT_USER_ID)):
    from services.session_service import session_service
    session_service.clear_session(session_id, user_id=user_id)
    return {"success": True, "session_id": session_id}


@router.get("/history/{session_id}")
def get_history(session_id: str, user_id: str = Query(default=settings.DEFAULT_USER_ID)):
    from services.session_service import session_service
    history = session_service.get_history(session_id, user_id=user_id)
    return {"history": history, "session_id": session_id}


@router.get("/image/{filename}")
def serve_image(filename: str):
    import os
    from fastapi.responses import FileResponse
    if "/" in filename or "\\" in filename or ".." in filename or not filename:
        return {"error": "Invalid filename"}
    img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
    img_path = os.path.join(img_dir, filename)
    real_path = os.path.realpath(img_path)
    if not real_path.startswith(os.path.realpath(img_dir)):
        return {"error": "Invalid filename"}
    if os.path.exists(real_path):
        return FileResponse(real_path, media_type="image/png")
    return {"error": "Image not found"}
