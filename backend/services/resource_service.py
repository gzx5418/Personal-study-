from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

from config import settings


class ResourceService:
    """学习资源存储服务。"""

    def __init__(self) -> None:
        self._resources: dict[str, list[dict]] = {}
        self._file = os.path.join(os.path.dirname(settings.PROFILE_FILE), "resources.json")
        self._use_db = False
        try:
            from services.database import db
            self._db = db
            self._use_db = True
        except Exception:
            self._db = None
        if not self._use_db:
            self._load()

    def _load(self) -> None:
        if os.path.exists(self._file):
            with open(self._file, "r", encoding="utf-8") as f:
                self._resources = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._resources, f, ensure_ascii=False, indent=2)

    def save_resource(self, user_id: str, topic: str, resource_type: str, content: str, **extra) -> dict:
        now = time.time()
        resource = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "course_id": extra.pop("course_id", settings.COURSE_ID),
            "topic": topic,
            "type": resource_type,
            "content": content,
            "created_at": now,
            "updated_at": now,
            "sources_used": extra.pop("sources_used", []),
            "resource_meta": extra.pop("resource_meta", {}),
            "source": extra.pop("source", "generated"),
        }
        if extra:
            resource.update(extra)
        if self._use_db:
            self._db.save_resource(resource)
        else:
            if user_id not in self._resources:
                self._resources[user_id] = []
            self._resources[user_id].append(resource)
            self._save()
        return resource

    def get_resources(self, user_id: str, resource_type: str | None = None, course_id: str | None = None) -> list[dict]:
        if self._use_db:
            return self._db.get_resources(user_id, resource_type, course_id)
        resources = self._resources.get(user_id, [])
        if resource_type and resource_type != "all":
            resources = [r for r in resources if r["type"] == resource_type]
        if course_id:
            resources = [r for r in resources if r.get("course_id") == course_id]
        return sorted(resources, key=lambda r: r.get("created_at", 0), reverse=True)

    def get_resource(self, user_id: str, resource_id: str) -> dict | None:
        if self._use_db:
            return self._db.get_resource(user_id, resource_id)
        for r in self._resources.get(user_id, []):
            if r["id"] == resource_id:
                return r
        return None

    def update_resource_content(self, resource_id: str, user_id: str, content: str) -> None:
        if self._use_db:
            self._db.update_resource_content(resource_id, user_id, content)
        else:
            for r in self._resources.get(user_id, []):
                if r["id"] == resource_id:
                    r["content"] = content
                    r["updated_at"] = time.time()
                    break

    def delete_resource(self, user_id: str, resource_id: str) -> bool:
        if self._use_db:
            return self._db.delete_resource(user_id, resource_id)
        resources = self._resources.get(user_id, [])
        for i, r in enumerate(resources):
            if r["id"] == resource_id:
                resources.pop(i)
                self._save()
                return True
        return False

    def record_event(
        self,
        user_id: str,
        resource_id: str,
        event_type: str,
        course_id: str = "",
        source_page: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._use_db:
            self._db.record_resource_event(user_id, resource_id, event_type, course_id, source_page, payload)

    def get_events(self, user_id: str, resource_id: str | None = None) -> list[dict]:
        if self._use_db:
            return self._db.get_resource_events(user_id, resource_id)
        return []


resource_service = ResourceService()
