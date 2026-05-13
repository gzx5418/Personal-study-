from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from core.context import UnifiedContext
from core.orchestrator import orchestrator

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{user_id}")
async def get_profile(user_id: str):
    from services.profile_service import profile_service
    return profile_service.get_profile(user_id)


@router.post("/extract")
async def extract_profile(req: ProfileExtractRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="profile",
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.put("/{user_id}")
async def update_profile(user_id: str, updates: dict):
    from services.profile_service import profile_service
    return profile_service.update_profile(user_id, updates)


@router.get("/check/{user_id}")
async def check_profile(user_id: str):
    from agents.profile_builder import ProfileBuilderAgent
    builder = ProfileBuilderAgent()
    return await builder.check_and_start(user_id)


@router.post("/build")
async def build_profile(req: BuildProfileRequest):
    from services.profile_service import profile_service
    from services.session_service import session_service

    session_service.add_message(req.session_id, "user", req.message, user_id=req.user_id)
    history = session_service.get_history(req.session_id, user_id=req.user_id)

    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="profile_build",
        history=history,
        profile_context={"text": profile_service.get_profile_context_text(req.user_id)},
        metadata={"mode": req.mode},
    )

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
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


class ProfileExtractRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_id: str = settings.DEFAULT_USER_ID


class BuildProfileRequest(BaseModel):
    message: str = ""
    session_id: str = "default"
    user_id: str = settings.DEFAULT_USER_ID
    mode: str = "guided"
