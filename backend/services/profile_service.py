from __future__ import annotations

import json
import os
import time
from typing import Any

from config import settings


class ProfileService:
    """学生画像服务 — 对话驱动的无感画像构建。"""

    DEFAULT_PROFILE = {
        "name": "学生用户",
        "background": "",
        "goal": "",
        "knowledge_level": "beginner",
        "learning_style": [],
        "weak_points": [],
        "strong_points": [],
        "daily_time": "",
        "learning_pace": "",
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
        except Exception:
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
            return data
        if user_id not in self._profiles:
            self._profiles[user_id] = {**self.DEFAULT_PROFILE, "created_at": time.time()}
        return self._profiles[user_id]

    def update_profile(self, user_id: str, updates: dict) -> dict:
        profile = self.get_profile(user_id)
        self._deep_merge(profile, updates)
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
        if topic not in profile["weak_points"]:
            profile["weak_points"].append(topic)
            profile["updated_at"] = time.time()
            if self._use_db:
                self._db.save_profile(user_id, profile)
            else:
                self._save()

    def remove_weak_point(self, user_id: str, topic: str) -> None:
        profile = self.get_profile(user_id)
        if topic in profile["weak_points"]:
            profile["weak_points"].remove(topic)
            profile["updated_at"] = time.time()
            if self._use_db:
                self._db.save_profile(user_id, profile)
            else:
                self._save()

    def get_profile_context_text(self, user_id: str) -> str:
        profile = self.get_profile(user_id)
        parts = []
        if profile.get("background"):
            parts.append(f"专业背景: {profile['background']}")
        if profile.get("goal"):
            parts.append(f"学习目标: {profile['goal']}")
        if profile.get("knowledge_level"):
            parts.append(f"知识水平: {profile['knowledge_level']}")
        if profile.get("learning_style"):
            parts.append(f"学习风格: {', '.join(profile['learning_style'])}")
        if profile.get("weak_points"):
            parts.append(f"薄弱知识点: {', '.join(profile['weak_points'])}")
        if profile.get("strong_points"):
            parts.append(f"擅长知识点: {', '.join(profile['strong_points'])}")
        return "\n".join(parts)

    @staticmethod
    def _deep_merge(base: dict, update: dict) -> dict:
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ProfileService._deep_merge(base[k], v)
            else:
                base[k] = v
        return base


profile_service = ProfileService()
