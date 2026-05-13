from __future__ import annotations

import os
import re
import time
from typing import AsyncIterator

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field

from core.context import UnifiedContext
from core.orchestrator import orchestrator
from config import settings

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
    resource_type: str = "lecture"
    topic: str
    user_id: str = settings.DEFAULT_USER_ID
    session_id: str = "default"
    num_questions: int = 5
    course_id: str = settings.COURSE_ID


class ResourcePlanRequest(BaseModel):
    message: str
    user_id: str = settings.DEFAULT_USER_ID
    session_id: str = "default"
    course_id: str = settings.COURSE_ID


class ResourceEventRequest(BaseModel):
    user_id: str = settings.DEFAULT_USER_ID
    resource_id: str
    event_type: str
    course_id: str = settings.COURSE_ID
    source_page: str = ""
    payload: dict = Field(default_factory=dict)


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
        active_capability="generate",
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
async def list_resources(user_id: str, type: str = "all", course_id: str = ""):
    from services.resource_service import resource_service
    resources = resource_service.get_resources(
        user_id,
        type if type != "all" else None,
        course_id=course_id or None,
    )
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
    try:
        from services.resource_service import resource_service

        resource = resource_service.get_resource(user_id, resource_id)
        if resource:
            file_name = resource.get("file_name") or ""
            ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

            if ext in ("pdf", "docx"):
                file_path = os.path.join(UPLOADS_DIR, f"{resource_id}.{ext}")
                if os.path.exists(file_path):
                    os.remove(file_path)

            if os.path.exists(UPLOADS_DIR):
                for f in os.listdir(UPLOADS_DIR):
                    if f.startswith(f"{resource_id}_img_"):
                        try:
                            os.remove(os.path.join(UPLOADS_DIR, f))
                        except Exception:
                            pass

        ok = resource_service.delete_resource(user_id, resource_id)
        return {"success": ok}
    except Exception as e:
        return {"success": False, "error": str(e)}


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


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(settings.DEFAULT_USER_ID),
    topic: str = Form(""),
    course_id: str = Form(settings.COURSE_ID),
):
    from services.resource_service import resource_service

    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_bytes = await file.read()

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return {"error": f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB"}

    if ext == "pdf":
        content = _extract_pdf_text(file_bytes)
        resource_type = "document"
    elif ext == "docx":
        content = ""  # Will be extracted after save (needs resource ID for images)
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
        return {"error": f"不支持的文件类型: .{ext}"}

    if not topic:
        topic = filename.rsplit(".", 1)[0] if "." in filename else filename

    # Add filename header for non-code files
    if ext not in CODE_EXTS:
        content = f"# {filename}\n\n{content}"

    saved = resource_service.save_resource(
        user_id=user_id,
        topic=topic,
        resource_type=resource_type,
        content=content,
        file_name=filename,
        source="upload",
        course_id=course_id,
    )

    # Save original binary and extract content for DOCX/PDF
    if ext in ("pdf", "docx"):
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        file_path = os.path.join(UPLOADS_DIR, f"{saved['id']}.{ext}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        if ext == "docx":
            content = _extract_docx_text(file_bytes, saved['id'])
            resource_service.update_resource_content(saved['id'], user_id, content)

    return {"success": True, "resource": saved, "text_length": len(content)}


@router.post("/event")
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


@router.get("/file/{user_id}/{resource_id}")
async def serve_resource_file(user_id: str, resource_id: str):
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

    if not os.path.exists(file_path):
        return JSONResponse({"error": "Original file not found"}, status_code=404)

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
    )
