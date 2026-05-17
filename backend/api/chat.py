from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.context import UnifiedContext
from core.orchestrator import orchestrator
from core.stream_bus import StreamBus
from config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_id: str = settings.DEFAULT_USER_ID
    capability: str = "chat"
    knowledge_bases: list[str] = Field(default_factory=list)
    image_base64: str = ""
    file_content: str = ""
    file_name: str = ""
    course_id: str = settings.COURSE_ID
    llm_model: str = ""
    reasoning_model: str = ""
    vision_model: str = ""
    embedding_model: str = ""


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: list[dict] = Field(default_factory=list)


@router.post("")
async def chat(req: ChatRequest) -> StreamingResponse:
    from services.profile_service import profile_service
    from services.mastery_service import mastery_service
    from services.session_service import session_service

    image_url = ""
    if req.image_base64:
        import base64, os, time
        img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
        os.makedirs(img_dir, exist_ok=True)
        filename = f"img_{int(time.time())}_{req.session_id}.png"
        filepath = os.path.join(img_dir, filename)
        try:
            img_data = base64.b64decode(req.image_base64)
            with open(filepath, "wb") as f:
                f.write(img_data)
            image_url = f"/api/chat/image/{filename}"
        except Exception:
            pass

    user_msg = req.message
    if image_url:
        user_msg = f"{user_msg}\n[用户上传了一张图片: {image_url}]" if user_msg else f"[用户上传了一张图片: {image_url}]"

    session_service.add_message(req.session_id, "user", user_msg, user_id=req.user_id)

    profile = profile_service.get_profile(req.user_id)
    mastery_summary = mastery_service.get_mastery_summary(req.user_id)
    history = session_service.get_history(req.session_id, user_id=req.user_id)

    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=user_msg,
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

    stream = await orchestrator.dispatch(ctx)

    async def event_generator() -> AsyncIterator[str]:
        collected = []
        async for event in stream.subscribe():
            yield event.to_sse()
            if event.type.value == "content":
                collected.append(event.data.get("text", ""))

        full_response = "".join(collected)
        if full_response:
            session_service.add_message(req.session_id, "assistant", full_response, user_id=req.user_id)

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
    from services.profile_service import profile_service
    from services.mastery_service import mastery_service
    from services.session_service import session_service

    session_service.add_message(req.session_id, "user", req.message, user_id=req.user_id)

    profile = profile_service.get_profile(req.user_id)
    mastery_summary = mastery_service.get_mastery_summary(req.user_id)
    history = session_service.get_history(req.session_id, user_id=req.user_id)

    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
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

    result = await orchestrator.dispatch_sync(ctx)
    if not result.get("success", True):
        response = f"Error: {result.get('error', 'Unknown error')}"
    else:
        response = result.get("response", "") or result.get("question", "")
    if response:
        session_service.add_message(req.session_id, "assistant", response, user_id=req.user_id)

    return ChatResponse(
        session_id=req.session_id,
        response=response,
        sources=result.get("sources", []),
    )


@router.get("/sessions/{user_id}")
async def list_sessions(user_id: str):
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
async def delete_session(session_id: str, user_id: str = Query(default=settings.DEFAULT_USER_ID)):
    from services.session_service import session_service
    session_service.clear_session(session_id, user_id=user_id)
    return {"success": True, "session_id": session_id}


@router.get("/history/{session_id}")
async def get_history(session_id: str, user_id: str = Query(default=settings.DEFAULT_USER_ID)):
    from services.session_service import session_service
    history = session_service.get_history(session_id, user_id=user_id)
    return {"history": history, "session_id": session_id}


@router.get("/image/{filename}")
async def serve_image(filename: str):
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
