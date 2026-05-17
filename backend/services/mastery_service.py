from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any

from config import settings

logger = logging.getLogger("zhixue.mastery")


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

    def analyze_weak_topics(
        self,
        user_id: str,
        threshold: float = 0.6,
    ) -> list[dict]:
        user_data = self.get_user_mastery(user_id)
        now = time.time()
        weak = []

        for topic_id, topic in user_data.items():
            level = topic["level"]
            if level >= threshold:
                continue

            last_practice = topic.get("last_practice")
            days_since = 0.0
            if last_practice:
                days_since = (now - last_practice) / 86400

            retention = self.calculate_forgetting_curve(days_since, level)
            attempts = topic["attempts"]
            accuracy = topic["correct"] / attempts if attempts > 0 else 0.0
            history = topic.get("history", [])
            recent_trend = self._calculate_trend(history)

            weak.append({
                "topic_id": topic_id,
                "mastery_level": level,
                "mastery_label": self._get_label(level),
                "retention_rate": retention,
                "days_since_practice": round(days_since, 1),
                "attempts": attempts,
                "accuracy": accuracy,
                "recent_trend": recent_trend,
                "gap": threshold - level,
                "urgency": self._calculate_urgency(level, days_since, retention),
            })

        weak.sort(key=lambda x: x["urgency"], reverse=True)
        logger.info(f"用户 {user_id} 分析到 {len(weak)} 个薄弱知识点 (阈值={threshold})")
        return weak

    def get_learning_priority(self, user_id: str) -> list[dict]:
        user_data = self.get_user_mastery(user_id)
        now = time.time()
        priorities = []

        for topic_id, topic in user_data.items():
            level = topic["level"]
            last_practice = topic.get("last_practice")
            days_since = 0.0
            if last_practice:
                days_since = (now - last_practice) / 86400

            retention = self.calculate_forgetting_curve(days_since, level)
            forgetting_urgency = 1.0 - retention
            mastery_gap = max(0, 0.8 - level)
            attempts = topic["attempts"]
            accuracy = topic["correct"] / attempts if attempts > 0 else 0.0
            accuracy_factor = 1.0 - accuracy if accuracy > 0 else 1.0

            priority_score = (
                forgetting_urgency * 0.4
                + mastery_gap * 0.35
                + accuracy_factor * 0.15
                + min(days_since / 30, 1.0) * 0.1
            )

            priorities.append({
                "topic_id": topic_id,
                "mastery_level": level,
                "retention_rate": retention,
                "days_since_practice": round(days_since, 1),
                "priority_score": round(priority_score, 4),
                "reason": self._determine_priority_reason(
                    level, days_since, retention, accuracy
                ),
            })

        priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        logger.info(f"用户 {user_id} 计算了 {len(priorities)} 个知识点的学习优先级")
        return priorities

    @staticmethod
    def calculate_forgetting_curve(
        days_since_practice: float,
        initial_mastery: float,
    ) -> float:
        if days_since_practice <= 0:
            return initial_mastery

        decay_rate = 0.3 + (1.0 - initial_mastery) * 0.5
        stability = 1.0 + initial_mastery * 5.0
        t = days_since_practice / stability
        retention = initial_mastery * math.exp(-decay_rate * t)

        return max(0.0, min(1.0, retention))

    @staticmethod
    def _calculate_trend(history: list[dict], window: int = 5) -> str:
        if len(history) < 2:
            return "insufficient_data"

        recent = history[-window:]
        if len(recent) < 2:
            return "insufficient_data"

        levels = [h["new_level"] for h in recent]
        diffs = [levels[i + 1] - levels[i] for i in range(len(levels) - 1)]
        avg_diff = sum(diffs) / len(diffs)

        if avg_diff > 0.02:
            return "improving"
        elif avg_diff < -0.02:
            return "declining"
        return "stable"

    @staticmethod
    def _calculate_urgency(
        level: float,
        days_since: float,
        retention: float,
    ) -> float:
        level_factor = 1.0 - level
        recency_factor = min(days_since / 14, 1.0)
        retention_factor = 1.0 - retention
        return round(level_factor * 0.4 + recency_factor * 0.3 + retention_factor * 0.3, 4)

    @staticmethod
    def _determine_priority_reason(
        level: float,
        days_since: float,
        retention: float,
        accuracy: float,
    ) -> str:
        reasons = []
        if level < 0.3:
            reasons.append("基础薄弱")
        elif level < 0.5:
            reasons.append("掌握不足")
        elif level < 0.8:
            reasons.append("尚未精通")

        if days_since > 14:
            reasons.append("较长时间未练习")
        elif days_since > 7:
            reasons.append("需要及时复习")

        if retention < level * 0.7:
            reasons.append("遗忘风险高")

        if accuracy < 0.5 and accuracy > 0:
            reasons.append("正确率偏低")

        return "；".join(reasons) if reasons else "常规复习"

    @staticmethod
    def _get_label(level: float) -> str:
        for label, (low, high) in MasteryService.MASTERY_LEVELS.items():
            if low <= level < high:
                return label
        return "expert"


mastery_service = MasteryService()
