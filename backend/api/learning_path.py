from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from fastapi import APIRouter
from pydantic import BaseModel

from config import settings

router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])


@dataclass
class PathNode:
    id: str
    title: str
    status: str
    mastery_level: float
    priority: float
    prerequisites: list[str] = field(default_factory=list)
    estimated_time: int = 0
    forgetting_rate: float = 1.0


class PhaseInfo(BaseModel):
    phase: str
    title: str
    nodes: list[dict]
    progress: float
    total_nodes: int
    completed_nodes: int


class TimelineResponse(BaseModel):
    user_id: str
    phases: list[PhaseInfo]
    overall_progress: float
    total_nodes: int


class GraphNode(BaseModel):
    id: str
    label: str
    status: str
    mastery_level: float
    group: str


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    user_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RecommendationItem(BaseModel):
    topic_id: str
    title: str
    reason: str
    priority_score: float
    mastery_level: float
    retention_rate: float
    estimated_time: int
    expected_improvement: float


class RecommendationsResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]
    generated_at: float


class ReviewItem(BaseModel):
    topic_id: str
    title: str
    scheduled_time: float
    interval_days: int
    easiness_factor: float
    overdue_days: float
    priority: float
    estimated_time: int


class SpacedRepetitionResponse(BaseModel):
    user_id: str
    due_reviews: list[ReviewItem]
    upcoming_reviews: list[ReviewItem]
    statistics: dict


def _get_path_nodes(course_id: str, user_id: str) -> list[PathNode]:
    from services.knowledge_graph import knowledge_graph_service
    from services.mastery_service import mastery_service
    from services.spaced_repetition_service import spaced_repetition_service

    path = knowledge_graph_service.get_learning_path(
        course_id,
        mastery=mastery_service.get_user_mastery(user_id),
    )
    now = time.time()
    nodes = []

    for item in path:
        topic_id = item["id"]
        mastery_level = item["mastery_level"]
        last_practice = mastery_service.get_topic_mastery(user_id, topic_id).get("last_practice")
        days_since = 0.0
        if last_practice:
            days_since = (now - last_practice) / 86400

        retention = mastery_service.calculate_forgetting_curve(days_since, mastery_level)
        priority_data = mastery_service.get_learning_priority(user_id)
        priority_score = 0.0
        for p in priority_data:
            if p["topic_id"] == topic_id:
                priority_score = p["priority_score"]
                break

        difficulty = item.get("difficulty", 1)
        base_time = 15 + difficulty * 10
        if mastery_level < 0.3:
            estimated_time = int(base_time * 1.5)
        elif mastery_level < 0.6:
            estimated_time = int(base_time * 1.0)
        else:
            estimated_time = int(base_time * 0.6)

        nodes.append(PathNode(
            id=topic_id,
            title=item.get("name", topic_id),
            status=item["status"],
            mastery_level=mastery_level,
            priority=priority_score,
            prerequisites=item.get("prerequisites", []),
            estimated_time=estimated_time,
            forgetting_rate=retention,
        ))

    return nodes


def _estimate_improvement(current_mastery: float, attempts: int) -> float:
    if current_mastery < 0.3:
        return 0.25
    elif current_mastery < 0.5:
        return 0.15
    elif current_mastery < 0.7:
        return 0.10
    elif current_mastery < 0.85:
        return 0.05
    return 0.02


def _to_timeline_view(path_data: list[PathNode]) -> dict:
    chapter_map: dict[str, list[PathNode]] = {}
    for node in path_data:
        chapter = node.id.rsplit("_", 1)[0] if "_" in node.id else "general"
        for prefix in ["chapter", "ch", "unit", "mod"]:
            if node.id.startswith(prefix):
                parts = node.id.split("_")
                if len(parts) >= 2:
                    chapter = "_".join(parts[:2])
                break

        if chapter not in chapter_map:
            chapter_map[chapter] = []
        chapter_map[chapter].append(node)

    sorted_keys = sorted(chapter_map.keys())
    phase_labels = ["基础入门", "核心概念", "进阶提升", "高级应用", "综合实践"]

    phases = []
    for i, key in enumerate(sorted_keys):
        group = chapter_map[key]
        completed = sum(1 for n in group if n.status == "mastered")
        progress = completed / len(group) if group else 0.0
        label = phase_labels[i] if i < len(phase_labels) else f"阶段 {i + 1}"

        phases.append({
            "phase": key,
            "title": label,
            "nodes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "status": n.status,
                    "mastery_level": n.mastery_level,
                    "priority": n.priority,
                    "prerequisites": n.prerequisites,
                    "estimated_time": n.estimated_time,
                    "forgetting_rate": n.forgetting_rate,
                }
                for n in group
            ],
            "progress": round(progress, 4),
            "total_nodes": len(group),
            "completed_nodes": completed,
        })

    total = len(path_data)
    mastered = sum(1 for n in path_data if n.status == "mastered")

    return {
        "phases": phases,
        "overall_progress": round(mastered / total, 4) if total else 0.0,
        "total_nodes": total,
    }


def _to_graph_view(path_data: list[PathNode]) -> dict:
    status_group = {
        "mastered": "mastered",
        "in_progress": "learning",
        "weak": "learning",
        "ready": "pending",
        "blocked": "blocked",
    }

    nodes = []
    for n in path_data:
        nodes.append({
            "id": n.id,
            "label": n.title,
            "status": n.status,
            "mastery_level": n.mastery_level,
            "group": status_group.get(n.status, "pending"),
        })

    edges = []
    for n in path_data:
        for pre in n.prerequisites:
            edges.append({"source": pre, "target": n.id})

    return {"nodes": nodes, "edges": edges}


def _build_spaced_repetition_data(user_id: str) -> dict:
    from services.spaced_repetition_service import spaced_repetition_service
    from services.mastery_service import mastery_service
    from services.knowledge_graph import knowledge_graph_service

    now = time.time()
    graph_service = knowledge_graph_service
    all_nodes = graph_service.get_all_nodes(settings.COURSE_ID)
    node_map = {n["id"]: n for n in all_nodes}

    due_items = []
    upcoming_items = []

    due_reviews = spaced_repetition_service.get_due_reviews(user_id)
    for review in due_reviews:
        topic_id = review["topic_id"]
        node_info = node_map.get(topic_id, {})
        title = node_info.get("name", topic_id)
        difficulty = node_info.get("difficulty", 1)

        mastery = mastery_service.get_topic_mastery(user_id, topic_id)
        mastery_level = mastery.get("level", 0)
        base_time = 5 + difficulty * 3
        est_time = max(3, round(base_time * (1.0 + (1.0 - mastery_level) * 0.5)))

        due_items.append({
            "topic_id": topic_id,
            "title": title,
            "scheduled_time": 0,
            "interval_days": review.get("interval_days", 0),
            "easiness_factor": review.get("easiness_factor", 2.5),
            "overdue_days": review.get("overdue_days", 0),
            "priority": review.get("priority", 0),
            "estimated_time": est_time,
        })

    stats = spaced_repetition_service.get_statistics(user_id)

    return {
        "due_reviews": due_items,
        "upcoming_reviews": [],
        "statistics": stats,
    }


@router.get("/timeline/{user_id}")
async def get_timeline(user_id: str, course_id: str = settings.COURSE_ID):
    path_data = _get_path_nodes(course_id, user_id)
    result = _to_timeline_view(path_data)
    return {"user_id": user_id, **result}


@router.get("/graph/{user_id}")
async def get_graph(user_id: str, course_id: str = settings.COURSE_ID):
    path_data = _get_path_nodes(course_id, user_id)
    result = _to_graph_view(path_data)
    return {"user_id": user_id, **result}


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, course_id: str = settings.COURSE_ID):
    from services.mastery_service import mastery_service

    mastery_data = mastery_service.get_user_mastery(user_id)
    recommendations = _calculate_recommendations_with_data(mastery_data, course_id)
    return {"user_id": user_id, "recommendations": recommendations, "generated_at": time.time()}


def _calculate_recommendations_with_data(mastery_data: dict, course_id: str) -> list[dict]:
    from services.mastery_service import mastery_service
    from services.knowledge_graph import knowledge_graph_service

    path = knowledge_graph_service.get_learning_path(course_id, mastery=mastery_data)
    path_map = {p["id"]: p for p in path}
    now = time.time()
    recommendations = []

    for topic_id, topic_data in mastery_data.items():
        node = path_map.get(topic_id)
        if not node:
            continue

        level = topic_data.get("level", 0)
        attempts = topic_data.get("attempts", 0)
        last_practice = topic_data.get("last_practice")
        days_since = (now - last_practice) / 86400 if last_practice else 999

        retention = mastery_service.calculate_forgetting_curve(days_since, level)
        forgetting_urgency = 1.0 - retention
        mastery_gap = max(0, 0.8 - level)
        accuracy = topic_data.get("correct", 0) / attempts if attempts > 0 else 0.0
        accuracy_factor = 1.0 - accuracy if accuracy > 0 else 1.0

        priority_score = round(
            forgetting_urgency * 0.4 + mastery_gap * 0.35 + accuracy_factor * 0.15 + min(days_since / 30, 1.0) * 0.1,
            4,
        )

        if level >= 0.85 and retention >= 0.7:
            continue

        reasons = []
        if level < 0.3:
            reasons.append("基础薄弱，需要优先学习")
        elif level < 0.5:
            reasons.append("掌握不足，建议重点巩固")
        elif level < 0.7:
            reasons.append("尚未精通，继续练习可提升")

        if retention < level * 0.7:
            reasons.append("遗忘风险高，建议及时复习")

        if days_since > 14:
            reasons.append(f"已 {int(days_since)} 天未复习")
        elif days_since > 7:
            reasons.append("超过一周未练习")

        if accuracy < 0.5 and accuracy > 0:
            reasons.append("正确率偏低")

        prereqs = node.get("prerequisites", [])
        prereqs_met = all(mastery_data.get(pr, {}).get("level", 0) >= 0.5 for pr in prereqs)
        if not prereqs_met:
            reasons.append("前置知识点尚未掌握")

        difficulty = node.get("difficulty", 1)
        base_time = 15 + difficulty * 10
        if level < 0.3:
            est_time = int(base_time * 1.5)
        elif level < 0.6:
            est_time = int(base_time * 1.0)
        else:
            est_time = int(base_time * 0.6)

        expected_imp = _estimate_improvement(level, attempts)

        recommendations.append({
            "topic_id": topic_id,
            "title": node.get("name", topic_id),
            "reason": "；".join(reasons) if reasons else "常规推荐",
            "priority_score": priority_score,
            "mastery_level": level,
            "retention_rate": round(retention, 4),
            "estimated_time": est_time,
            "expected_improvement": round(expected_imp, 4),
        })

    recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
    return recommendations[:10]


@router.get("/spaced-repetition/{user_id}")
async def get_spaced_repetition(user_id: str):
    result = _build_spaced_repetition_data(user_id)
    return {"user_id": user_id, **result}
