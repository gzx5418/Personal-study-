from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("zhixue.knowledge_api")

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class UpdateKnowledgeRequest(BaseModel):
    documents: list[dict]
    version_note: str = ""


class RollbackRequest(BaseModel):
    target_version: int


@router.get("/list")
async def list_knowledge_bases():
    from services.rag_service import rag_service

    bases = rag_service.list_knowledge_bases_detailed()
    return {"knowledge_bases": bases}


@router.get("/{kb_name}/versions")
async def get_versions(kb_name: str):
    from services.database import db

    versions = db.get_kb_versions(kb_name)
    current = db.get_current_version(kb_name)
    return {
        "kb_name": kb_name,
        "versions": versions,
        "current_version": current["version"] if current else None,
    }


@router.post("/{kb_name}/update")
async def update_knowledge_base(kb_name: str, req: UpdateKnowledgeRequest):
    from services.rag_service import rag_service

    result = rag_service.update_knowledge_base(kb_name, req.documents, req.version_note)
    return result


@router.post("/{kb_name}/rollback")
async def rollback_knowledge_base(kb_name: str, req: RollbackRequest):
    from services.rag_service import rag_service

    result = rag_service.rollback_knowledge_base(kb_name, req.target_version)
    return result
