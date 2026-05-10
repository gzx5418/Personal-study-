from __future__ import annotations

import os
import time
from typing import AsyncIterator

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.context import UnifiedContext
from core.orchestrator import orchestrator
from config import settings

router = APIRouter(prefix="/api/resources", tags=["resources"])


class GenerateRequest(BaseModel):
    resource_type: str = "lecture"
    topic: str
    user_id: str = "default"
    session_id: str = "default"
    num_questions: int = 5
    course_id: str = "python_programming"


@router.post("/generate")
async def generate_resource(req: GenerateRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=f"生成{req.resource_type}: {req.topic}",
        active_capability="generate",
        config_overrides={
            "resource_type": req.resource_type,
            "topic": req.topic,
            "num_questions": req.num_questions,
            "course_id": req.course_id,
        },
    )

    stream = await orchestrator.dispatch(ctx)

    async def event_generator() -> AsyncIterator[str]:
        async for event in stream.subscribe():
            yield event.to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/plan")
async def plan_resources(req: ResourcePlanRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=req.message,
        active_capability="resource_plan",
        config_overrides={"course_id": req.course_id},
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.get("/list/{user_id}")
async def list_resources(user_id: str, type: str = "all"):
    from services.resource_service import resource_service
    resources = resource_service.get_resources(user_id, type if type != "all" else None)
    return {"resources": resources}


@router.get("/detail/{user_id}/{resource_id}")
async def get_resource(user_id: str, resource_id: str):
    from services.resource_service import resource_service
    resource = resource_service.get_resource(user_id, resource_id)
    if not resource:
        return {"error": "Resource not found"}
    return resource


@router.delete("/{user_id}/{resource_id}")
async def delete_resource(user_id: str, resource_id: str):
    from services.resource_service import resource_service
    ok = resource_service.delete_resource(user_id, resource_id)
    return {"success": ok}


@router.post("/knowledge/upload")
async def upload_knowledge(course_id: str = "", content: str = "", filename: str = "manual"):
    from services.database import db
    from services.rag_service import rag_service

    if not content:
        return {"error": "No content provided"}

    if not course_id:
        course_id = settings.COURSE_ID

    chunks = []
    lines = content.split("\n")
    chunk_size = 50
    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i:i + chunk_size])
        if chunk.strip():
            chunk_id = db.save_knowledge_chunk(course_id, filename, chunk, len(chunks))
            chunks.append(chunk_id)

    rag_service._load_simple_kb()

    return {"success": True, "chunks_created": len(chunks), "course_id": course_id}


@router.post("/upload")
async def upload_resource(
    user_id: str = "default",
    topic: str = "",
    resource_type: str = "document",
    content: str = "",
    file_name: str = "",
):
    from services.resource_service import resource_service

    if not content:
        return {"error": "No content provided"}

    if not topic:
        topic = file_name or "未命名资源"

    saved = resource_service.save_resource(
        user_id=user_id,
        topic=topic,
        resource_type=resource_type,
        content=content,
        file_name=file_name,
        source="upload",
    )

    return {"success": True, "resource": saved}


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF解析失败: {e}]"


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        return "\n\n".join(paragraphs)
    except Exception as e:
        return f"[DOCX解析失败: {e}]"


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form("default"),
    topic: str = Form(""),
):
    from services.resource_service import resource_service

    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        return {"error": "文件大小不能超过 10MB"}

    if ext == "pdf":
        content = _extract_pdf_text(file_bytes)
        resource_type = "document"
    elif ext == "docx":
        content = _extract_docx_text(file_bytes)
        resource_type = "document"
    elif ext in ("txt", "md", "csv", "yaml", "yml", "json", "log"):
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("gbk")
            except:
                content = file_bytes.decode("latin-1")
        resource_type = "document"
    elif ext in ("py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h", "hpp", "html", "css", "sql", "sh", "bat", "ps1", "r", "rb", "go", "rs", "swift", "kt", "php", "pl", "lua"):
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")
        lang_map = {"py": "python", "js": "javascript", "ts": "typescript", "jsx": "jsx", "tsx": "tsx", "java": "java", "cpp": "cpp", "c": "c", "h": "c", "html": "html", "css": "css", "json": "json", "sql": "sql", "sh": "bash", "rb": "ruby", "go": "go", "rs": "rust", "swift": "swift", "kt": "kotlin", "php": "php", "pl": "perl", "lua": "lua"}
        lang = lang_map.get(ext, ext)
        content = f"# {filename}\n\n```{lang}\n{content}\n```"
        resource_type = "code"
    else:
        return {"error": f"不支持的文件类型: .{ext}"}

    if not topic:
        topic = filename.rsplit(".", 1)[0] if "." in filename else filename

    content_preview = content[:500] + ("..." if len(content) > 500 else "")
    if ext not in ("py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h", "hpp", "html", "css", "sql", "sh", "bat", "ps1", "r", "rb", "go", "rs", "swift", "kt", "php", "pl", "lua"):
        content = f"# {filename}\n\n{content}"

    saved = resource_service.save_resource(
        user_id=user_id,
        topic=topic,
        resource_type=resource_type,
        content=content,
        file_name=filename,
        source="upload",
    )

    return {"success": True, "resource": saved, "text_length": len(content)}


class ResourcePlanRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: str = "default"
    course_id: str = "python_programming"
