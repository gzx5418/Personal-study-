from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

app = FastAPI(
    title="智学助手 API",
    description="基于多智能体的高校个性化学习资源生成与学习路径规划系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.chat import router as chat_router
from api.profile import router as profile_router
from api.resources import router as resources_router
from api.path import router as path_router
from api.evaluation import router as evaluation_router

app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(resources_router)
app.include_router(path_router)
app.include_router(evaluation_router)


@app.get("/")
async def root():
    return {"name": "智学助手", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def frontend_config():
    return {
        "app_name": settings.APP_NAME,
        "default_user_id": settings.DEFAULT_USER_ID,
        "default_course_id": settings.COURSE_ID,
        "api_base_url": settings.API_BASE_URL,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
    }


@app.get("/api/stats")
async def stats():
    from services.llm_service import llm_service
    result = {"token_stats": llm_service.get_stats()}
    try:
        from services.database import db
        result["db_stats"] = db.get_stats()
    except Exception:
        pass
    return result


@app.get("/api/courses")
async def list_courses():
    from services.rag_service import rag_service
    from services.knowledge_graph import knowledge_graph_service

    kb_list = rag_service.list_knowledge_bases()
    courses = []
    for course_id in kb_list:
        nodes = knowledge_graph_service.get_all_nodes(course_id)
        graph = knowledge_graph_service.get_graph(course_id)
        courses.append({
            "id": course_id,
            "name": graph.graph.get("course_name", course_id) if graph else course_id,
            "node_count": len(nodes),
        })
    return {"courses": courses, "current": settings.COURSE_ID}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
