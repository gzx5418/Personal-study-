from __future__ import annotations

import json
import os
import time
from typing import Any

from config import settings


class MasteryService:
    """掌握度追踪服务 — 项目核心创新点之一。"""

    MASTERY_LEVELS = {
        "novice": (0.0, 0.3),
        "beginner": (0.3, 0.5),
        "intermediate": (0.5, 0.7),
        "advanced": (0.7, 0.85),
        "expert": (0.85, 1.0),
    }

    DEFAULT_TOPIC = {
        "level": 0.0,
        "attempts": 0,
        "correct": 0,
        "last_practice": None,
        "history": [],
    }

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict]] = {}
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
        if os.path.exists(settings.MASTERY_FILE):
            with open(settings.MASTERY_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(settings.MASTERY_FILE), exist_ok=True)
        with open(settings.MASTERY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_user_mastery(self, user_id: str) -> dict[str, dict]:
        if self._use_db:
            return self._db.get_user_mastery(user_id)
        return self._data.get(user_id, {})

    def get_topic_mastery(self, user_id: str, topic_id: str) -> dict:
        if self._use_db:
            user_data = self._db.get_user_mastery(user_id)
            return user_data.get(topic_id, {**self.DEFAULT_TOPIC})
        user_data = self._data.get(user_id, {})
        return user_data.get(topic_id, {**self.DEFAULT_TOPIC})

    def update_mastery(
        self,
        user_id: str,
        topic_id: str,
        correct: bool,
        difficulty: float = 0.5,
    ) -> dict:
        topic = self.get_topic_mastery(user_id, topic_id)
        old_level = topic["level"]

        if correct:
            topic["level"] = min(1.0, topic["level"] + (1 - topic["level"]) * 0.2 * (1 + difficulty))
            topic["correct"] += 1
        else:
            topic["level"] = max(0.0, topic["level"] * 0.7 * (1 - difficulty * 0.3))

        topic["attempts"] += 1
        topic["last_practice"] = time.time()
        topic["history"].append({
            "timestamp": time.time(),
            "correct": correct,
            "old_level": old_level,
            "new_level": topic["level"],
            "difficulty": difficulty,
        })

        if len(topic["history"]) > 50:
            topic["history"] = topic["history"][-50:]

        if self._use_db:
            self._db.save_mastery(user_id, topic_id, topic)
        else:
            if user_id not in self._data:
                self._data[user_id] = {}
            self._data[user_id][topic_id] = topic
            self._save()

        return {
            "topic_id": topic_id,
            "old_level": old_level,
            "new_level": topic["level"],
            "delta": topic["level"] - old_level,
            "mastery_label": self._get_label(topic["level"]),
        }

    def apply_decay(self, user_id: str, decay_hours: float = 72.0) -> list[dict]:
        user_data = self.get_user_mastery(user_id)
        now = time.time()
        decayed = []

        for topic_id, topic in user_data.items():
            last = topic.get("last_practice")
            if not last:
                continue
            hours_since = (now - last) / 3600
            if hours_since > decay_hours:
                decay_factor = 0.99 ** (hours_since / 24)
                old_level = topic["level"]
                topic["level"] = max(0.1, topic["level"] * decay_factor)
                if abs(topic["level"] - old_level) > 0.01:
                    decayed.append({"topic_id": topic_id, "old": old_level, "new": topic["level"]})
                    if self._use_db:
                        self._db.save_mastery(user_id, topic_id, topic)

        if decayed and not self._use_db:
            self._save()
        return decayed

    def get_weak_topics(self, user_id: str, threshold: float = 0.5) -> list[dict]:
        user_data = self.get_user_mastery(user_id)
        weak = []
        for topic_id, topic in user_data.items():
            if topic["level"] < threshold:
                weak.append({
                    "topic_id": topic_id,
                    "level": topic["level"],
                    "label": self._get_label(topic["level"]),
                    "attempts": topic["attempts"],
                })
        return sorted(weak, key=lambda x: x["level"])

    def get_mastery_summary(self, user_id: str) -> dict:
        user_data = self.get_user_mastery(user_id)
        if not user_data:
            return {"total_topics": 0, "avg_level": 0, "distribution": {}}

        levels = [t["level"] for t in user_data.values()]
        distribution = {}
        for label, (low, high) in self.MASTERY_LEVELS.items():
            count = sum(1 for l in levels if low <= l < high)
            distribution[label] = count

        return {
            "total_topics": len(user_data),
            "avg_level": sum(levels) / len(levels),
            "weak_count": sum(1 for l in levels if l < 0.5),
            "strong_count": sum(1 for l in levels if l >= 0.7),
            "distribution": distribution,
        }

    @staticmethod
    def _get_label(level: float) -> str:
        for label, (low, high) in MasteryService.MASTERY_LEVELS.items():
            if low <= level < high:
                return label
        return "expert"


mastery_service = MasteryService()
