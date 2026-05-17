from __future__ import annotations

from pydantic import BaseModel, Field

from config import settings


class ResourceEventRequest(BaseModel):
    user_id: str = settings.DEFAULT_USER_ID
    resource_id: str
    event_type: str
    course_id: str = settings.COURSE_ID
    source_page: str = ""
    payload: dict = Field(default_factory=dict)
