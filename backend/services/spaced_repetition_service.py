from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any

from config import settings

logger = logging.getLogger("zhixue.spaced_repetition")


class SpacedRepetitionService:

    MIN_EASINESS = 1.3
    DEFAULT_EASINESS = 2.5
    INITIAL_INTERVALS = [1, 6]

    def __init__(self) -> None:
        self._cards: dict[str, dict[str, dict]] = {}
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
        path = self._get_storage_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._cards = json.load(f)

    def _save(self) -> None:
        path = self._get_storage_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._cards, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_storage_path() -> str:
        return os.path.join(os.path.dirname(settings.MASTERY_FILE), "spaced_repetition.json")

    def get_card(self, user_id: str, topic_id: str) -> dict:
        user_cards = self._cards.get(user_id, {})
        return user_cards.get(topic_id, {
            "interval": 0,
            "easiness": self.DEFAULT_EASINESS,
            "repetitions": 0,
            "next_review": 0,
            "last_review": None,
            "review_history": [],
        })

    def review(
        self,
        user_id: str,
        topic_id: str,
        quality: int,
    ) -> dict:
        quality = max(0, min(5, quality))
        card = self.get_card(user_id, topic_id)

        old_interval = card["interval"]
        old_easiness = card["easiness"]

        card["repetitions"] += 1
        card["last_review"] = time.time()

        card["easiness"] = self._calculate_easiness(
            card["easiness"], quality
        )

        if quality < 3:
            card["repetitions"] = 0
            card["interval"] = 1
        else:
            if card["repetitions"] <= len(self.INITIAL_INTERVALS):
                card["interval"] = self.INITIAL_INTERVALS[card["repetitions"] - 1]
            else:
                card["interval"] = self._calculate_interval(
                    card["interval"], card["easiness"]
                )

        card["next_review"] = time.time() + card["interval"] * 86400

        card["review_history"].append({
            "timestamp": time.time(),
            "quality": quality,
            "old_interval": old_interval,
            "new_interval": card["interval"],
            "old_easiness": old_easiness,
            "new_easiness": card["easiness"],
        })

        if len(card["review_history"]) > 100:
            card["review_history"] = card["review_history"][-100:]

        self._save_card(user_id, topic_id, card)

        logger.info(
            f"用户 {user_id} 复习 {topic_id}: "
            f"quality={quality}, interval={card['interval']}天, "
            f"easiness={card['easiness']:.2f}"
        )

        return {
            "topic_id": topic_id,
            "interval_days": card["interval"],
            "easiness_factor": round(card["easiness"], 2),
            "next_review": card["next_review"],
            "next_review_in_days": card["interval"],
            "repetitions": card["repetitions"],
            "quality": quality,
        }

    @staticmethod
    def _calculate_easiness(current_easiness: float, quality: int) -> float:
        new_easiness = current_easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        return max(SpacedRepetitionService.MIN_EASINESS, new_easiness)

    @staticmethod
    def _calculate_interval(previous_interval: int, easiness: float) -> int:
        return max(1, math.ceil(previous_interval * easiness))

    def _save_card(self, user_id: str, topic_id: str, card: dict) -> None:
        if self._use_db:
            self._save_card_db(user_id, topic_id, card)
        else:
            if user_id not in self._cards:
                self._cards[user_id] = {}
            self._cards[user_id][topic_id] = card
            self._save()

    def _save_card_db(self, user_id: str, topic_id: str, card: dict) -> None:
        conn = self._db._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO sr_cards
                   (user_id, topic_id, interval_val, easiness, repetitions, next_review, last_review, review_history)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    topic_id,
                    card["interval"],
                    card["easiness"],
                    card["repetitions"],
                    card["next_review"],
                    card.get("last_review"),
                    json.dumps(card.get("review_history", []), ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _load_card_db(self, user_id: str, topic_id: str) -> dict | None:
        conn = self._db._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM sr_cards WHERE user_id = ? AND topic_id = ?",
                (user_id, topic_id),
            ).fetchone()
            if row:
                return {
                    "interval": row["interval_val"],
                    "easiness": row["easiness"],
                    "repetitions": row["repetitions"],
                    "next_review": row["next_review"],
                    "last_review": row["last_review"],
                    "review_history": json.loads(row["review_history"] or "[]"),
                }
            return None
        finally:
            conn.close()

    def get_due_reviews(self, user_id: str) -> list[dict]:
        now = time.time()
        due = []

        if self._use_db:
            due = self._get_due_reviews_db(user_id, now)
        else:
            user_cards = self._cards.get(user_id, {})
            for topic_id, card in user_cards.items():
                next_review = card.get("next_review", 0)
                if next_review <= now:
                    overdue_days = (now - next_review) / 86400 if next_review > 0 else 0
                    due.append({
                        "topic_id": topic_id,
                        "interval_days": card["interval"],
                        "easiness_factor": round(card["easiness"], 2),
                        "repetitions": card["repetitions"],
                        "overdue_days": round(overdue_days, 1),
                        "priority": self._calculate_review_priority(card, overdue_days),
                    })

        due.sort(key=lambda x: x["priority"], reverse=True)
        logger.info(f"用户 {user_id} 有 {len(due)} 个待复习知识点")
        return due

    def _get_due_reviews_db(self, user_id: str, now: float) -> list[dict]:
        conn = self._db._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sr_cards WHERE user_id = ? AND next_review <= ?",
                (user_id, now),
            ).fetchall()
            due = []
            for row in rows:
                next_review = row["next_review"]
                overdue_days = (now - next_review) / 86400 if next_review > 0 else 0
                card = {
                    "interval": row["interval_val"],
                    "easiness": row["easiness"],
                    "repetitions": row["repetitions"],
                }
                due.append({
                    "topic_id": row["topic_id"],
                    "interval_days": row["interval_val"],
                    "easiness_factor": round(row["easiness"], 2),
                    "repetitions": row["repetitions"],
                    "overdue_days": round(overdue_days, 1),
                    "priority": self._calculate_review_priority(card, overdue_days),
                })
            return due
        finally:
            conn.close()

    @staticmethod
    def _calculate_review_priority(card: dict, overdue_days: float) -> float:
        interval = max(1, card["interval"])
        overdue_ratio = overdue_days / interval
        easiness_factor = 2.5 / max(1.3, card["easiness"])
        return round(overdue_ratio * 0.7 + easiness_factor * 0.3, 4)

    def schedule_review_queue(
        self,
        user_id: str,
        weak_topics: list[dict],
        max_daily: int = 10,
    ) -> list[dict]:
        now = time.time()
        queue = []

        for topic in weak_topics:
            topic_id = topic["topic_id"]
            card = self.get_card(user_id, topic_id)

            if card["next_review"] <= now or card["repetitions"] == 0:
                recommended_quality = self._estimate_quality(
                    topic.get("mastery_level", 0),
                    topic.get("accuracy", 0),
                )
                projected = self._project_schedule(card, recommended_quality)

                queue.append({
                    "topic_id": topic_id,
                    "mastery_level": topic.get("mastery_level", 0),
                    "urgency": topic.get("urgency", 0),
                    "current_interval": card["interval"],
                    "projected_interval": projected["interval"],
                    "projected_next_review": projected["next_review"],
                    "recommended_quality": recommended_quality,
                    "review_type": "new" if card["repetitions"] == 0 else "overdue",
                })

        queue.sort(key=lambda x: (x["review_type"] == "overdue", x["urgency"]), reverse=True)
        queue = queue[:max_daily]

        for i, item in enumerate(queue):
            item["scheduled_position"] = i + 1
            item["estimated_review_time_min"] = self._estimate_review_time(
                item["mastery_level"], item["review_type"]
            )

        logger.info(f"用户 {user_id} 调度了 {len(queue)} 个知识点到复习队列")
        return queue

    @staticmethod
    def _estimate_quality(mastery_level: float, accuracy: float) -> int:
        if mastery_level < 0.2:
            return 1
        elif mastery_level < 0.4:
            return 2
        elif mastery_level < 0.6:
            return 3
        elif mastery_level < 0.8 and accuracy > 0.6:
            return 4
        elif accuracy > 0.8:
            return 5
        return 3

    def _project_schedule(self, card: dict, quality: int) -> dict:
        new_easiness = self._calculate_easiness(card["easiness"], quality)

        if quality < 3:
            new_interval = 1
            new_reps = 0
        else:
            new_reps = card["repetitions"] + 1
            if new_reps <= len(self.INITIAL_INTERVALS):
                new_interval = self.INITIAL_INTERVALS[new_reps - 1]
            else:
                new_interval = self._calculate_interval(
                    card["interval"], new_easiness
                )

        return {
            "interval": new_interval,
            "next_review": time.time() + new_interval * 86400,
            "easiness": round(new_easiness, 2),
        }

    @staticmethod
    def _estimate_review_time(mastery_level: float, review_type: str) -> int:
        base = 10 if review_type == "new" else 5
        difficulty_factor = 1.0 + (1.0 - mastery_level) * 0.5
        return max(3, round(base * difficulty_factor))

    def get_statistics(self, user_id: str) -> dict:
        if self._use_db:
            return self._get_statistics_db(user_id)

        user_cards = self._cards.get(user_id, {})
        if not user_cards:
            return {"total_cards": 0, "due_count": 0, "avg_easiness": 0}

        now = time.time()
        due_count = sum(
            1 for c in user_cards.values() if c.get("next_review", 0) <= now
        )
        easiness_values = [c["easiness"] for c in user_cards.values()]

        return {
            "total_cards": len(user_cards),
            "due_count": due_count,
            "avg_easiness": round(sum(easiness_values) / len(easiness_values), 2),
            "min_easiness": round(min(easiness_values), 2),
            "max_easiness": round(max(easiness_values), 2),
            "cards_by_repetitions": self._count_by_repetitions(user_cards),
        }

    def _get_statistics_db(self, user_id: str) -> dict:
        conn = self._db._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sr_cards WHERE user_id = ?", (user_id,)
            ).fetchall()
            if not rows:
                return {"total_cards": 0, "due_count": 0, "avg_easiness": 0}

            now = time.time()
            due_count = sum(1 for r in rows if r["next_review"] <= now)
            easiness_values = [r["easiness"] for r in rows]

            return {
                "total_cards": len(rows),
                "due_count": due_count,
                "avg_easiness": round(sum(easiness_values) / len(easiness_values), 2),
                "min_easiness": round(min(easiness_values), 2),
                "max_easiness": round(max(easiness_values), 2),
            }
        finally:
            conn.close()

    @staticmethod
    def _count_by_repetitions(cards: dict[str, dict]) -> dict[str, int]:
        buckets = {"0": 0, "1-5": 0, "6-10": 0, "10+": 0}
        for card in cards.values():
            reps = card["repetitions"]
            if reps == 0:
                buckets["0"] += 1
            elif reps <= 5:
                buckets["1-5"] += 1
            elif reps <= 10:
                buckets["6-10"] += 1
            else:
                buckets["10+"] += 1
        return buckets


spaced_repetition_service = SpacedRepetitionService()
