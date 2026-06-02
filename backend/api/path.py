from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import settings
from core.context import UnifiedContext
from core.orchestrator import orchestrator

router = APIRouter(prefix="/api/path", tags=["path"])


class PathPlanRequest(BaseModel):
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    session_id: str = Field(default="default", max_length=64)
    course_id: str = Field(default=settings.COURSE_ID, max_length=64)
    message: str = Field(default="请为我规划学习路径", max_length=20000)
    reason: str = Field(default="", max_length=2000)


@router.post("/plan")
async def plan_path(req: PathPlanRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="path_plan",
        config_overrides={"course_id": req.course_id},
        metadata={"course_id": req.course_id},
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.post("/adjust")
async def adjust_path(req: PathPlanRequest):
    reason = req.reason or "用户手动触发路径调整"
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=f"根据最新学习情况调整路径。调整原因：{reason}",
        active_capability="path_plan",
        config_overrides={"course_id": req.course_id},
        metadata={"course_id": req.course_id},
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.get("/graph/{course_id}")
def get_graph(course_id: str):
    from services.knowledge_graph import knowledge_graph_service
    nodes = knowledge_graph_service.get_all_nodes(course_id)
    chapters = knowledge_graph_service.get_chapters(course_id)
    return {"nodes": nodes, "chapters": chapters}
