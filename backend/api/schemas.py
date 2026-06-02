from __future__ import annotations

import re
from fastapi import HTTPException
from pydantic import BaseModel, Field

from config import settings

SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-.]+$')


def validate_user_id(user_id: str) -> str:
    """Validate user_id to prevent injection. Only allow alphanumeric, underscore, hyphen, dot."""
    if not user_id or len(user_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not SAFE_ID_PATTERN.match(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    return user_id


class ResourceEventRequest(BaseModel):
    user_id: str = Field(default=settings.DEFAULT_USER_ID, max_length=64)
    resource_id: str = Field(..., min_length=1, max_length=128)
    event_type: str = Field(..., min_length=1, max_length=64)
    course_id: str = Field(default=settings.COURSE_ID, max_length=64)
    source_page: str = Field(default="", max_length=128)
    payload: dict = Field(default_factory=dict)
