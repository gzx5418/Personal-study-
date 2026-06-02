from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from config import settings

logger = logging.getLogger("zhixue.profile")


class ProfileService:
    """学生画像服务 — 对话驱动的无感画像构建。"""

    DEFAULT_PROFILE = {
        "name": "学生用户",
        "major_or_background": {
            "value": "",
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "learning_goal": {
            "value": "",
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "knowledge_level": {
            "value": "beginner",
            "confidence": 0.2,
            "evidence": [],
            "updated_at": None,
        },
        "learning_style": {
            "value": [],
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "weak_points": {
            "value": [],
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "strong_points": {
            "value": [],
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "time_budget": {
            "value": "",
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "pace_preference": {
            "value": "",
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "modality_preference": {
            "value": "mixed",
            "confidence": 0.0,
            "evidence": [],
            "updated_at": None,
        },
        "preferences": {
            "resource_type": "mixed",
            "pace": "normal",
            "detail_level": "medium",
        },
        "stats": {
            "total_messages": 0,
            "total_practice": 0,
            "study_hours": 0,
        },
        "updated_at": None,
    }

    def __init__(self) -> None:
        self._profiles: dict[str, dict] = {}
        self._use_db = False
        try:
            from services.database import db
            self._db = db
            self._use_db = True
        except Exception as e:
            logger.warning(f"数据库初始化失败，降级为文件存储: {e}")
            self._db = None
        if not self._use_db:
            self._load()

    def _load(self) -> None:
        if os.path.exists(settings.PROFILE_FILE):
            with open(settings.PROFILE_FILE, "r", encoding="utf-8") as f:
                self._profiles = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(settings.PROFILE_FILE), exist_ok=True)
        with open(settings.PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._profiles, f, ensure_ascii=False, indent=2)

    def get_profile(self, user_id: str) -> dict:
        if self._use_db:
            data = self._db.get_profile(user_id)
            if data is None:
                data = {**self.DEFAULT_PROFILE, "created_at": time.time()}
                self._db.save_profile(user_id, data)
            return self._normalize_profile(data)
        if user_id not in self._profiles:
            self._profiles[user_id] = {**self.DEFAULT_PROFILE, "created_at": time.time()}
        self._profiles[user_id] = self._normalize_profile(self._profiles[user_id])
        return self._profiles[user_id]

    def update_profile(self, user_id: str, updates: dict) -> dict:
        profile = self.get_profile(user_id)
        normalized_updates = self._normalize_updates(updates)
        self._deep_merge(profile, normalized_updates)
        profile = self._normalize_profile(profile)
        profile["updated_at"] = time.time()
        if self._use_db:
            self._db.save_profile(user_id, profile)
        else:
            self._profiles[user_id] = profile
            self._save()
        return profile

    def increment_stat(self, user_id: str, stat_key: str, value: int = 1) -> None:
        profile = self.get_profile(user_id)
        if stat_key in profile.get("stats", {}):
            profile["stats"][stat_key] += value
            profile["updated_at"] = time.time()
            if self._use_db:
                self._db.save_profile(user_id, profile)
            else:
                self._save()

    def add_weak_point(self, user_id: str, topic: str) -> None:
        profile = self.get_profile(user_id)
        weak_points = profile["weak_points"]["value"]
        if topic not in weak_points:
            weak_points.append(topic)
            profile["weak_points"]["updated_at"] = time.time()
            profile["updated_at"] = time.time()
            if self._use_db:
                self._db.save_profile(user_id, profile)
            else:
                self._save()

    def remove_weak_point(self, user_id: str, topic: str) -> None:
        profile = self.get_profile(user_id)
        weak_points = profile["weak_points"]["value"]
        if topic in weak_points:
            weak_points.remove(topic)
            profile["weak_points"]["updated_at"] = time.time()
            profile["updated_at"] = time.time()
            if self._use_db:
                self._db.save_profile(user_id, profile)
            else:
                self._save()

    def get_profile_context_text(self, user_id: str) -> str:
        profile = self.get_profile(user_id)
        parts = []
        if profile["major_or_background"]["value"]:
            parts.append(f"专业背景: {profile['major_or_background']['value']}")
        if profile["learning_goal"]["value"]:
            parts.append(f"学习目标: {profile['learning_goal']['value']}")
        if profile["knowledge_level"]["value"]:
            parts.append(f"知识水平: {profile['knowledge_level']['value']}")
        if profile["learning_style"]["value"]:
            parts.append(f"学习风格: {', '.join(profile['learning_style']['value'])}")
        if profile["weak_points"]["value"]:
            parts.append(f"薄弱知识点: {', '.join(profile['weak_points']['value'])}")
        if profile["strong_points"]["value"]:
            parts.append(f"擅长知识点: {', '.join(profile['strong_points']['value'])}")
        if profile["time_budget"]["value"]:
            parts.append(f"时间预算: {profile['time_budget']['value']}")
        if profile["pace_preference"]["value"]:
            parts.append(f"学习节奏: {profile['pace_preference']['value']}")
        if profile["modality_preference"]["value"]:
            parts.append(f"偏好模态: {profile['modality_preference']['value']}")
        return "\n".join(parts)

    def get_field_value(self, profile: dict, field_name: str, default: Any = "") -> Any:
        field = profile.get(field_name, {})
        if isinstance(field, dict) and "value" in field:
            return field.get("value", default)
        return field or default

    @staticmethod
    def _deep_merge(base: dict, update: dict) -> dict:
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ProfileService._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    def _normalize_profile(self, profile: dict) -> dict:
        profile = {**self.DEFAULT_PROFILE, **profile}

        legacy_map = {
            "background": "major_or_background",
            "goal": "learning_goal",
            "daily_time": "time_budget",
            "learning_pace": "pace_preference",
        }
        for legacy_key, field_key in legacy_map.items():
            legacy_value = profile.pop(legacy_key, None)
            if legacy_value and not profile[field_key]["value"]:
                profile[field_key]["value"] = legacy_value
                profile[field_key]["confidence"] = max(profile[field_key]["confidence"], 0.6)
                profile[field_key]["updated_at"] = profile.get("updated_at")

        for field_name in (
            "major_or_background",
            "learning_goal",
            "knowledge_level",
            "learning_style",
            "weak_points",
            "strong_points",
            "time_budget",
            "pace_preference",
            "modality_preference",
        ):
            profile[field_name] = self._normalize_field(profile.get(field_name), self.DEFAULT_PROFILE[field_name])

        # Compatibility aliases for the current frontend modules.
        profile["background"] = profile["major_or_background"]["value"]
        profile["goal"] = profile["learning_goal"]["value"]
        profile["daily_time"] = profile["time_budget"]["value"]
        profile["learning_pace"] = profile["pace_preference"]["value"]
        profile["learning_style_legacy"] = profile["learning_style"]["value"]
        profile["weak_points_legacy"] = profile["weak_points"]["value"]
        profile["strong_points_legacy"] = profile["strong_points"]["value"]

        if not isinstance(profile.get("preferences"), dict):
            profile["preferences"] = {**self.DEFAULT_PROFILE["preferences"]}
        profile["preferences"]["pace"] = profile["pace_preference"]["value"] or profile["preferences"].get("pace", "normal")
        profile["preferences"]["resource_type"] = profile["modality_preference"]["value"] or profile["preferences"].get("resource_type", "mixed")

        return profile

    @staticmethod
    def _normalize_field(value: Any, default_field: dict) -> dict:
        now = time.time()
        if isinstance(value, dict) and "value" in value:
            field = {**default_field, **value}
            if field.get("evidence") is None:
                field["evidence"] = []
            return field
        field = dict(default_field)
        field["value"] = value if value is not None else default_field["value"]
        if value not in (None, "", []):
            field["confidence"] = max(field.get("confidence", 0.0), 0.6)
            field["updated_at"] = default_field.get("updated_at") or now
        return field

    def _normalize_updates(self, updates: dict) -> dict:
        normalized = {}
        field_aliases = {
            "background": "major_or_background",
            "goal": "learning_goal",
            "daily_time": "time_budget",
            "learning_pace": "pace_preference",
            "resource_type": "modality_preference",
        }
        structured_fields = {
            "major_or_background",
            "learning_goal",
            "knowledge_level",
            "learning_style",
            "weak_points",
            "strong_points",
            "time_budget",
            "pace_preference",
            "modality_preference",
        }

        for key, value in updates.items():
            target_key = field_aliases.get(key, key)
            if target_key in structured_fields:
                normalized[target_key] = self._wrap_field_value(value)
            else:
                normalized[target_key] = value
        return normalized

    @staticmethod
    def _wrap_field_value(value: Any) -> dict:
        if isinstance(value, dict) and "value" in value:
            field = dict(value)
            field.setdefault("confidence", 0.7 if field.get("value") not in ("", [], None) else 0.0)
            field.setdefault("evidence", [])
            field.setdefault("updated_at", time.time())
            return field
        return {
            "value": value,
            "confidence": 0.7 if value not in ("", [], None) else 0.0,
            "evidence": [],
            "updated_at": time.time() if value not in ("", [], None) else None,
        }


profile_service = ProfileService()
