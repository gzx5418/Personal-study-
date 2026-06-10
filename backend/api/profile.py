from __future__ import annotations

from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from core.context import UnifiedContext
from core.orchestrator import orchestrator
from api.schemas import validate_user_id
from fastapi.concurrency import run_in_threadpool
from limiter import limiter

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Whitelist of fields allowed in profile updates
ALLOWED_PROFILE_FIELDS = {
    "major_or_background", "background",
    "learning_goal", "goal",
    "knowledge_level",
    "learning_style",
    "weak_points",
    "strong_points",
    "time_budget", "daily_time",
    "pace_preference", "learning_pace",
    "modality_preference",
    "preferences",
    "name",
}


class ProfileExtractRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000)
    session_id: str = Field(default="default", max_length=64)
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)


class BuildProfileRequest(BaseModel):
    message: str = Field(default="", max_length=20000)
    session_id: str = Field(default="default", max_length=64)
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    mode: str = Field(default="guided", max_length=32)


class ProfileUpdateRequest(BaseModel):
    updates: dict[str, Any] = Field(..., max_length=50)


@router.get("/{user_id}")
async def get_profile(user_id: str):
    from services.profile_service import profile_service
    validate_user_id(user_id)
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
async def update_profile(user_id: str, req: ProfileUpdateRequest):
    from services.profile_service import profile_service

    validate_user_id(user_id)

    # Only allow whitelisted fields
    filtered = {k: v for k, v in req.updates.items() if k in ALLOWED_PROFILE_FIELDS}
    if not filtered:
        return {"error": "No valid fields to update"}

    return profile_service.update_profile(user_id, filtered)


@router.get("/check/{user_id}")
async def check_profile(user_id: str):
    from core.agent import agent_registry
    validate_user_id(user_id)
    builder = agent_registry.get_agent("profile_build")
    return await builder.check_and_start(user_id)


@router.post("/build")
@limiter.limit("20/minute")
async def build_profile(req: BuildProfileRequest, request: Request):
    from services.profile_service import profile_service
    from services.session_service import session_service

    await run_in_threadpool(session_service.add_message, req.session_id, "user", req.message, user_id=req.user_id)
    history = await run_in_threadpool(session_service.get_history, req.session_id, user_id=req.user_id)

    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="profile_build",
        history=history,
        profile_context={"text": await run_in_threadpool(profile_service.get_profile_context_text, req.user_id)},
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
            await run_in_threadpool(session_service.add_message, req.session_id, "assistant", full_response, user_id=req.user_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
