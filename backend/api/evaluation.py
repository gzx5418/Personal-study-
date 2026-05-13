from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import settings
from core.context import UnifiedContext
from core.orchestrator import orchestrator
from core.stream_bus import StreamBus

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class QuizSubmitRequest(BaseModel):
    user_id: str = settings.DEFAULT_USER_ID
    session_id: str = "default"
    course_id: str = settings.COURSE_ID
    quiz_results: list[dict] = Field(default_factory=list)


class QuizParseRequest(BaseModel):
    content: str
    user_id: str = settings.DEFAULT_USER_ID


class DiagnosticRequest(BaseModel):
    user_id: str = settings.DEFAULT_USER_ID
    session_id: str = "default"
    message: str = "请诊断我的学习情况"


class ResourceEventRequest(BaseModel):
    user_id: str = settings.DEFAULT_USER_ID
    resource_id: str
    event_type: str
    course_id: str = settings.COURSE_ID
    source_page: str = ""
    payload: dict = Field(default_factory=dict)


@router.post("/parse-quiz")
async def parse_quiz(req: QuizParseRequest):
    from services.llm_service import llm_service

    prompt = f"""从以下练习题文本中提取结构化数据。输出JSON数组，每个元素包含：
- question: 题目文本
- options: 选项数组（每个选项是字符串）
- answer: 正确答案（选项字母，如A/B/C/D）
- topic: 知识点（如有）

练习题文本：
{req.content[:3000]}

只输出JSON数组，不要其他内容。"""

    try:
        result = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        import json
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            questions = json.loads(result[start:end])
        else:
            questions = []
        return {"questions": questions}
    except Exception as e:
        return {"questions": [], "error": str(e)}


@router.post("/submit")
async def submit_quiz(req: QuizSubmitRequest):
    from services.mastery_service import mastery_service
    from agents.evaluator import EvaluatorAgent
    from agents.path_planner import PathPlannerAgent

    evaluator = EvaluatorAgent()
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message="提交练习结果",
        active_capability="evaluate",
        config_overrides={"quiz_results": req.quiz_results, "course_id": req.course_id},
        metadata={"course_id": req.course_id},
    )
    stream = StreamBus()
    eval_result = await evaluator.process(ctx, stream)

    mastery_summary = mastery_service.get_mastery_summary(req.user_id)
    weak_topics = mastery_service.get_weak_topics(req.user_id)

    path_result = None
    try:
        path_planner = PathPlannerAgent()
        path_ctx = UnifiedContext(
            session_id=req.session_id,
            user_id=req.user_id,
            user_message="根据最新掌握度调整学习路径",
            active_capability="path_plan",
            config_overrides={"course_id": req.course_id},
            metadata={"course_id": req.course_id},
        )
        path_stream = StreamBus()
        path_result = await path_planner.process(path_ctx, path_stream)
    except Exception:
        pass

    recommendations = []
    if weak_topics:
        for wt in weak_topics[:3]:
            recommendations.append({
                "topic": wt["topic_id"],
                "level": wt["level"],
                "suggestion": f"建议复习 {wt['topic_id']}，当前掌握度 {wt['level']:.0%}",
            })

    return {
        "evaluation": eval_result,
        "mastery_summary": mastery_summary,
        "weak_topics": weak_topics,
        "adjusted_path": path_result,
        "recommendations": recommendations,
    }


@router.post("/diagnose")
async def diagnose(req: DiagnosticRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="diagnostic",
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.get("/mastery/{user_id}")
async def get_mastery(user_id: str):
    from services.mastery_service import mastery_service
    return {
        "mastery": mastery_service.get_user_mastery(user_id),
        "summary": mastery_service.get_mastery_summary(user_id),
        "weak_topics": mastery_service.get_weak_topics(user_id),
    }


@router.post("/resource-event")
async def record_resource_event(req: ResourceEventRequest):
    from services.resource_service import resource_service

    resource_service.record_event(
        req.user_id,
        req.resource_id,
        req.event_type,
        course_id=req.course_id,
        source_page=req.source_page,
        payload=req.payload,
    )
    return {"success": True}
