from __future__ import annotations

import logging
import os
import re
import time
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from core.context import UnifiedContext
from core.orchestrator import orchestrator
from config import settings
from api.schemas import ResourceEventRequest

logger = logging.getLogger("zhixue.resources")

router = APIRouter(prefix="/api/resources", tags=["resources"])

# Code file extensions
CODE_EXTS = frozenset([
    "py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h", "hpp",
    "html", "css", "json", "sql", "sh", "bat", "ps1", "r", "rb",
    "go", "rs", "swift", "kt", "php", "pl", "lua",
])

# Text file extensions
TEXT_EXTS = frozenset(["txt", "md", "csv", "yaml", "yml", "log"])

# Extension → language map for code blocks
LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "jsx": "jsx",
    "tsx": "tsx", "java": "java", "cpp": "cpp", "c": "c", "h": "c",
    "html": "html", "css": "css", "json": "json", "sql": "sql", "sh": "bash",
    "rb": "ruby", "go": "go", "rs": "rust", "swift": "swift", "kt": "kotlin",
    "php": "php", "pl": "perl", "lua": "lua",
}

# Uploads directory
UPLOADS_DIR = os.path.join(os.path.dirname(settings.PROFILE_FILE), "uploads")


class GenerateRequest(BaseModel):
    resource_type: str = Field(default="lecture", max_length=64)
    topic: str = Field(..., min_length=1, max_length=500)
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    session_id: str = Field(default="default", max_length=64)
    num_questions: int = Field(default=5, gt=0, le=50)
    course_id: str = Field(default=settings.COURSE_ID, max_length=64)


class ResourcePlanRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000)
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    session_id: str = Field(default="default", max_length=64)
    course_id: str = Field(default=settings.COURSE_ID, max_length=64)


class RateRequest(BaseModel):
    user_id: str = Field(..., max_length=64)
    resource_id: str = Field(..., max_length=128)
    rating: int = Field(..., ge=1, le=5)


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


def _extract_docx_text(file_bytes: bytes, resource_id: str = "") -> str:
    try:
        import mammoth
        import io
        from markdownify import markdownify as md

        image_map = {}

        def convert_image(image):
            with image.open() as img_bytes:
                img_data = img_bytes.read()
                ext = (image.content_type or "image/png").split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                img_name = f"{resource_id}_img_{len(image_map)}.{ext}"
                os.makedirs(UPLOADS_DIR, exist_ok=True)
                img_path = os.path.join(UPLOADS_DIR, img_name)
                with open(img_path, "wb") as f:
                    f.write(img_data)
                url = f"/api/chat/image/{img_name}"
                image_map[img_name] = url
                return {"src": url}

        result = mammoth.convert_to_html(
            io.BytesIO(file_bytes),
            convert_image=mammoth.images.img_element(convert_image),
        )
        html = result.value
        markdown_text = md(html, heading_style="ATX")

        lines = markdown_text.split("\n")
        cleaned = [line for line in lines if line.strip()]
        return "\n".join(cleaned)
    except Exception as e:
        return f"[DOCX解析失败: {e}]"


def _decode_file(file_bytes: bytes, ext: str) -> str:
    """Decode file bytes to string, trying multiple encodings."""
    if ext == "md":
        pass  # Will be handled by the caller
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("latin-1")


@router.post("/generate")
async def generate_resource(req: GenerateRequest):
    ctx = UnifiedContext(
        session_id=req.session_id,
        user_id=req.user_id,
        user_message=f"生成{req.resource_type}: {req.topic}",
        active_capability="resource_orchestrator",
        config_overrides={
            "resource_type": req.resource_type,
            "topic": req.topic,
            "num_questions": req.num_questions,
            "course_id": req.course_id,
        },
        metadata={"course_id": req.course_id},
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
        metadata={"course_id": req.course_id},
    )
    result = await orchestrator.dispatch_sync(ctx)
    return result


@router.get("/list/{user_id}")
def list_resources(user_id: str, type: str = "all", course_id: str = ""):
    from services.resource_service import resource_service
    resources = resource_service.get_resources(
        user_id,
        type if type != "all" else None,
        course_id=course_id or None,
    )
    return {"resources": resources}


@router.get("/detail/{user_id}/{resource_id}")
def get_resource(user_id: str, resource_id: str):
    from services.resource_service import resource_service
    resource = resource_service.get_resource(user_id, resource_id)
    if not resource:
        return JSONResponse({"error": "Resource not found"}, status_code=404)
    return resource


@router.delete("/{user_id}/{resource_id}")
def delete_resource(user_id: str, resource_id: str):
    try:
        from services.resource_service import resource_service

        if not re.match(r'^[a-zA-Z0-9_-]+$', resource_id):
            return JSONResponse({"success": False, "error": "Invalid resource ID"}, status_code=400)

        resource = resource_service.get_resource(user_id, resource_id)
        if resource:
            file_name = resource.get("file_name") or ""
            ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

            uploads_real = os.path.realpath(UPLOADS_DIR)

            if ext in ("pdf", "docx"):
                file_path = os.path.join(UPLOADS_DIR, f"{resource_id}.{ext}")
                real_path = os.path.realpath(file_path)
                if real_path.startswith(uploads_real + os.sep) and os.path.exists(real_path):
                    os.remove(real_path)

            if os.path.exists(UPLOADS_DIR):
                for f in os.listdir(UPLOADS_DIR):
                    if f.startswith(f"{resource_id}_img_"):
                        try:
                            target = os.path.realpath(os.path.join(UPLOADS_DIR, f))
                            if target.startswith(uploads_real + os.sep):
                                os.remove(target)
                        except Exception:
                            pass

        ok = resource_service.delete_resource(user_id, resource_id)
        return {"success": ok}
    except Exception as e:
        return JSONResponse({"success": False, "error": "删除失败"}, status_code=500)


@router.post("/knowledge/upload")
def upload_knowledge(course_id: str = "", content: str = "", filename: str = "manual"):
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
def upload_resource(
    user_id: str = settings.DEFAULT_USER_ID,
    topic: str = "",
    resource_type: str = "document",
    content: str = "",
    file_name: str = "",
    course_id: str = settings.COURSE_ID,
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
        course_id=course_id,
    )

    return {"success": True, "resource": saved}


def _sanitize_filename(filename: str) -> str:
    """净化文件名，防止目录遍历和注入。"""
    if not filename:
        return "unnamed"
    # 移除路径分隔符
    filename = filename.replace("\\", "").replace("/", "")
    # 禁止 .. 序列
    filename = filename.replace("..", "")
    # 仅保留安全字符（字母、数字、中文、空格、连字符、点号、下划线）
    sanitized = re.sub(r'[^\w\u4e00-\u9fff\s\-.]', '', filename)
    sanitized = re.sub(r'\.{2,}', '.', sanitized)
    sanitized = sanitized.strip('. ')
    return sanitized[:255] or "unnamed"


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(settings.DEFAULT_USER_ID),
    topic: str = Form(""),
    course_id: str = Form(settings.COURSE_ID),
):
    from services.resource_service import resource_service

    filename = _sanitize_filename(file.filename or "unknown")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    if not re.match(r'^[\w\u4e00-\u9fff\s\-.]+$', filename):
        logger.warning(f"Invalid filename attempted: {file.filename}")
        return JSONResponse({"error": "文件名包含非法字符"}, status_code=400)
    
    file_bytes = await file.read()
    
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        logger.warning(f"File too large: {len(file_bytes)} bytes, max: {max_size}")
        return JSONResponse({"error": f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB"}, status_code=400)
    
    if len(file_bytes) == 0:
        return JSONResponse({"error": "文件内容为空"}, status_code=400)

    if ext == "pdf":
        content = _extract_pdf_text(file_bytes)
        resource_type = "document"
    elif ext == "docx":
        content = ""
        resource_type = "document"
    elif ext in TEXT_EXTS:
        content = _decode_file(file_bytes, ext)
        resource_type = "document"
    elif ext in CODE_EXTS:
        content = _decode_file(file_bytes, ext)
        lang = LANG_MAP.get(ext, ext)
        content = f"# {filename}\n\n```{lang}\n{content}\n```"
        resource_type = "code"
    else:
        logger.warning(f"Unsupported file type attempted: .{ext}")
        return JSONResponse({"error": f"不支持的文件类型: .{ext}"}, status_code=400)

    if not topic:
        topic = filename.rsplit(".", 1)[0] if "." in filename else filename

    if ext not in CODE_EXTS:
        content = f"# {filename}\n\n{content}"

    saved = await run_in_threadpool(
        resource_service.save_resource,
        user_id=user_id,
        topic=topic,
        resource_type=resource_type,
        content=content,
        file_name=filename,
        source="upload",
        course_id=course_id,
    )

    if ext in ("pdf", "docx"):
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        safe_resource_id = re.sub(r'[^a-zA-Z0-9_-]', '', saved['id'])
        file_path = os.path.join(UPLOADS_DIR, f"{safe_resource_id}.{ext}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        if ext == "docx":
            content = _extract_docx_text(file_bytes, safe_resource_id)
            resource_service.update_resource_content(safe_resource_id, user_id, content)
        
        logger.info(f"File uploaded: {filename} ({len(file_bytes)} bytes) by user {user_id}")

    return {"success": True, "resource": saved, "text_length": len(content)}


@router.post("/rate")
def rate_resource(req: RateRequest):
    from services.resource_service import resource_service

    if req.rating < 1 or req.rating > 5:
        return JSONResponse({"error": "评分范围为 1-5"}, status_code=400)

    resource = resource_service.get_resource(req.user_id, req.resource_id)
    if not resource:
        return JSONResponse({"error": "资源不存在"}, status_code=404)

    resource_service.record_event(
        req.user_id,
        req.resource_id,
        "rate",
        payload={"rating": req.rating},
    )

    logger.info(f"用户 {req.user_id} 对资源 {req.resource_id} 评分: {req.rating}")
    return {"success": True, "rating": req.rating}


@router.post("/event")
def record_resource_event(req: ResourceEventRequest):
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


@router.get("/file/{user_id}/{resource_id}")
def serve_resource_file(user_id: str, resource_id: str):
    from services.resource_service import resource_service

    if not re.match(r'^[a-zA-Z0-9_-]+$', resource_id):
        return JSONResponse({"error": "Invalid resource ID"}, status_code=400)

    resource = resource_service.get_resource(user_id, resource_id)
    if not resource:
        return JSONResponse({"error": "Resource not found"}, status_code=404)

    file_name = resource.get("file_name") or ""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    if ext == "pdf":
        file_path = os.path.join(UPLOADS_DIR, f"{resource_id}.pdf")
        media_type = "application/pdf"
    elif ext == "docx":
        file_path = os.path.join(UPLOADS_DIR, f"{resource_id}.docx")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        return JSONResponse({"error": "Only PDF and DOCX files can be served"}, status_code=400)

    # 路径遍历防护：确保解析后的真实路径仍在允许的 uploads 目录内
    real_path = os.path.realpath(file_path)
    uploads_real = os.path.realpath(UPLOADS_DIR)
    if not (real_path == uploads_real or real_path.startswith(uploads_real + os.sep)):
        logger.warning(f"Path traversal attempt: resource_id={resource_id}, real_path={real_path}")
        return JSONResponse({"error": "Access denied"}, status_code=403)

    if not os.path.exists(real_path):
        return JSONResponse({"error": "Original file not found"}, status_code=404)

    return FileResponse(
        real_path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
    )


@router.get("/pptx/{user_id}/{resource_id}")
def download_pptx(user_id: str, resource_id: str):
    from services.resource_service import resource_service
    from services.pptx_service import generate_pptx_from_outline

    if not re.match(r'^[a-zA-Z0-9_-]+$', resource_id):
        return JSONResponse({"error": "Invalid resource ID"}, status_code=400)

    resource = resource_service.get_resource(user_id, resource_id)
    if not resource:
        return JSONResponse({"error": "Resource not found"}, status_code=404)
    if resource.get("type") != "ppt_outline":
        return JSONResponse({"error": "Only PPT outline resources can be exported"}, status_code=400)

    pptx_bytes = generate_pptx_from_outline(
        resource.get("content") or "",
        resource.get("topic") or "个性化学习资源",
    )
    safe_name = re.sub(r'[\\/:*?"<>|]+', "_", resource.get("topic") or "learning_resource")
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pptx"'},
    )
