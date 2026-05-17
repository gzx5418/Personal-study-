from __future__ import annotations

import logging
import sys
import time
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("zhixue")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN != "*":
    ALLOWED_ORIGINS.append(settings.FRONTEND_ORIGIN)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("智学助手 API 启动中...")
    logger.info(f"LLM 模型: {settings.LLM_MODEL}")
    logger.info(f"监听地址: {settings.HOST}:{settings.PORT}")
    yield
    logger.info("智学助手 API 关闭中...")

app = FastAPI(
    title="智学助手 API",
    description="基于多智能体的高校个性化学习资源生成与学习路径规划系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )

from api.chat import router as chat_router
from api.profile import router as profile_router
from api.resources import router as resources_router
from api.path import router as path_router
from api.evaluation import router as evaluation_router
from api.learning_path import router as learning_path_router
from api.knowledge import router as knowledge_router

app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(resources_router)
app.include_router(path_router)
app.include_router(evaluation_router)
app.include_router(learning_path_router)
app.include_router(knowledge_router)


@app.get("/")
async def root():
    return {"name": "智学助手", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def frontend_config():
    from services.model_catalog import get_model_catalog

    return {
        "app_name": settings.APP_NAME,
        "default_user_id": settings.DEFAULT_USER_ID,
        "default_course_id": settings.COURSE_ID,
        "api_base_url": settings.API_BASE_URL,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "model_catalog": get_model_catalog(),
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
