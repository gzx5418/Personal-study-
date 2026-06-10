from __future__ import annotations

import json
import logging
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus
from config import settings

logger = logging.getLogger("zhixue.path_planner")


@register_agent("path_plan")
class PathPlannerAgent(BaseAgent):
    """学习路径规划 Agent — 项目核心创新点之一。
    
    基于知识依赖图（DAG）和掌握度，生成个性化学习路径。
    支持自适应调整：掌握度变化后自动更新路径。
    """

    def __init__(self) -> None:
        super().__init__(agent_name="path_planner_agent", module_name="path_planner")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("path_plan", "正在规划学习路径...")

        from services.knowledge_graph import knowledge_graph_service
        from services.mastery_service import mastery_service
        from services.profile_service import profile_service
        from services.spaced_repetition_service import spaced_repetition_service

        course_id = ctx.config_overrides.get("course_id", settings.COURSE_ID)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        profile = profile_service.get_profile(ctx.user_id)

        graph_path = knowledge_graph_service.get_learning_path(course_id, mastery)
        recommended = knowledge_graph_service.get_recommended_next(course_id, mastery)
        weak_topics = mastery_service.get_weak_topics(ctx.user_id)

        analyzed_weak = mastery_service.analyze_weak_topics(ctx.user_id)
        learning_priority = mastery_service.get_learning_priority(ctx.user_id)
        prerequisite_map = self._analyze_prerequisites(
            knowledge_graph_service.get_graph(course_id)
        )
        adaptive_path = self._build_adaptive_path(ctx.user_id, mastery)
        spaced_schedule = self._schedule_spaced_repetition(analyzed_weak)

        due_reviews = spaced_repetition_service.get_due_reviews(ctx.user_id)
        sr_stats = spaced_repetition_service.get_statistics(ctx.user_id)

        prompt = self.load_prompt("plan_path", {
            "profile": json.dumps(profile, ensure_ascii=False, indent=2),
            "mastery_summary": json.dumps(mastery_service.get_mastery_summary(ctx.user_id), ensure_ascii=False),
            "graph_path": json.dumps(graph_path, ensure_ascii=False, indent=2),
            "recommended": json.dumps(recommended, ensure_ascii=False, indent=2),
            "user_message": ctx.user_message,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ctx.user_message},
        ]

        result = await self.call_llm_json(messages, temperature=0.4)

        modality = profile.get("modality_preference", {}).get("value", "mixed")
        recommended_types = {
            "video": ["animation", "lecture", "quiz", "code_lab"],
            "animation": ["animation", "lecture", "quiz", "code_lab"],
            "slides": ["ppt_outline", "lecture", "quiz", "extended_reading"],
            "document": ["lecture", "extended_reading", "ppt_outline", "quiz"],
            "code": ["code_lab", "quiz", "lecture", "animation"],
        }.get(modality, ["lecture", "ppt_outline", "quiz", "extended_reading", "code_lab"])
        for stage in result.get("stages", []):
            if not stage.get("resources"):
                stage["resources"] = recommended_types
        if not result.get("path_adjustment_reason"):
            if weak_topics:
                topics = ", ".join(w["topic_id"] for w in weak_topics[:3])
                result["path_adjustment_reason"] = f"检测到 {topics} 为当前主要薄弱点，因此路径会优先补强这些知识点。"
            else:
                result["path_adjustment_reason"] = "当前路径主要依据知识依赖和已掌握情况生成，没有额外前移或延后。"

        result["graph_path"] = graph_path
        result["recommended_next"] = recommended
        result["mastery_summary"] = mastery_service.get_mastery_summary(ctx.user_id)
        result["weak_topics_ranked"] = weak_topics[:5]
        result["adaptive_path"] = adaptive_path
        result["analyzed_weak_topics"] = analyzed_weak[:10]
        result["learning_priority"] = learning_priority[:10]
        result["prerequisite_map"] = prerequisite_map
        result["spaced_repetition_schedule"] = spaced_schedule[:10]
        result["due_reviews"] = due_reviews[:10]
        result["sr_statistics"] = sr_stats

        logger.info(
            f"用户 {ctx.user_id} 路径规划完成: "
            f"{len(adaptive_path)} 个阶段, "
            f"{len(analyzed_weak)} 个薄弱点, "
            f"{len(due_reviews)} 个待复习"
        )

        stream.result(result)
        stream.stage_end("path_plan")
        return result

    def _build_adaptive_path(
        self,
        user_id: str,
        mastery_data: dict[str, dict],
    ) -> list[dict]:
        from services.knowledge_graph import knowledge_graph_service
        from services.mastery_service import mastery_service
        from services.spaced_repetition_service import spaced_repetition_service

        course_id = settings.COURSE_ID
        graph = knowledge_graph_service.get_graph(course_id)
        if graph is None:
            logger.warning(f"无法构建自适应路径: 课程 {course_id} 无知识图谱")
            return []

        analyzed_weak = mastery_service.analyze_weak_topics(user_id)
        prerequisite_map = self._analyze_prerequisites(graph)
        learning_priority = mastery_service.get_learning_priority(user_id)
        weak_ids = {w["topic_id"] for w in analyzed_weak}

        import networkx as nx
        topo_order = list(nx.topological_sort(graph))
        path = []
        phase_buffer: list[dict] = []
        phase_number = 1

        for node_id in topo_order:
            node_data = dict(graph.nodes[node_id])
            level = mastery_data.get(node_id, {}).get("level", 0)
            prereqs = list(graph.predecessors(node_id))
            prereq_met = all(
                mastery_data.get(p, {}).get("level", 0) >= 0.5 for p in prereqs
            )

            priority_info = next(
                (p for p in learning_priority if p["topic_id"] == node_id),
                {"priority_score": 0, "reason": ""},
            )
            retention = mastery_data.get(node_id, {}).get("level", 0)
            days_since = 0
            last_practice = mastery_data.get(node_id, {}).get("last_practice")
            if last_practice:
                import time as _time
                days_since = (_time.time() - last_practice) / 86400
            retention = mastery_service.calculate_forgetting_curve(days_since, level)

            if level >= 0.8:
                status = "mastered"
                action = "review"
            elif node_id in weak_ids:
                status = "weak"
                action = "strengthen"
            elif level >= 0.5:
                status = "in_progress"
                action = "continue"
            elif prereq_met:
                status = "ready"
                action = "learn"
            else:
                missing = [
                    p for p in prereqs
                    if mastery_data.get(p, {}).get("level", 0) < 0.5
                ]
                status = "blocked"
                action = "prerequisite_needed"
                prerequisite_map[node_id]["blocking_prereqs"] = missing

            phase_buffer.append({
                "topic_id": node_id,
                "name": node_data.get("name", node_id),
                "difficulty": node_data.get("difficulty", 1),
                "status": status,
                "action": action,
                "mastery_level": round(level, 3),
                "retention_rate": round(retention, 3),
                "priority_score": priority_info.get("priority_score", 0),
                "priority_reason": priority_info.get("reason", ""),
                "prerequisites": prereqs,
                "prereq_met": prereq_met,
            })

            if len(phase_buffer) >= 5 or (node_id == topo_order[-1] and phase_buffer):
                phase_label = self._determine_phase_label(phase_buffer)
                path.append({
                    "phase": phase_number,
                    "label": phase_label,
                    "topics": phase_buffer,
                    "topic_count": len(phase_buffer),
                    "weak_count": sum(1 for t in phase_buffer if t["status"] == "weak"),
                    "ready_count": sum(1 for t in phase_buffer if t["action"] == "learn"),
                })
                phase_buffer = []
                phase_number += 1

        logger.info(f"用户 {user_id} 构建自适应路径: {len(path)} 个阶段")
        return path

    def _analyze_prerequisites(
        self,
        knowledge_graph: Any,
    ) -> dict[str, dict]:
        if knowledge_graph is None:
            return {}

        import networkx as nx

        prereq_map: dict[str, dict] = {}
        graph = knowledge_graph

        for node_id in graph.nodes():
            predecessors = list(graph.predecessors(node_id))
            successors = list(graph.successors(node_id))

            ancestors = list(nx.ancestors(graph, node_id))
            descendants = list(nx.descendants(graph, node_id))

            in_degree = graph.in_degree(node_id)
            out_degree = graph.out_degree(node_id)

            depth = 0
            if ancestors:
                try:
                    depth = max(
                        len(p)
                        for p in nx.all_simple_paths(
                            graph.subgraph(set(ancestors) | {node_id}),
                            min(ancestors, key=lambda n: graph.in_degree(n)),
                            node_id,
                        )
                    )
                except (nx.NetworkXError, ValueError):
                    depth = len(ancestors)

            is_foundation = in_degree == 0 and out_degree > 0
            is_advanced = in_degree > 0 and out_degree == 0
            is_critical = out_degree >= 3

            prereq_map[node_id] = {
                "direct_prerequisites": predecessors,
                "direct_dependents": successors,
                "all_ancestors": ancestors,
                "all_descendants": descendants,
                "depth": depth,
                "is_foundation": is_foundation,
                "is_advanced": is_advanced,
                "is_critical": is_critical,
                "dependents_count": out_degree,
                "prerequisite_count": in_degree,
            }

        logger.info(f"分析前置知识依赖: {len(prereq_map)} 个知识点")
        return prereq_map

    def _schedule_spaced_repetition(
        self,
        weak_topics: list[dict],
    ) -> list[dict]:
        from services.spaced_repetition_service import spaced_repetition_service
        from services.profile_service import profile_service

        if not weak_topics:
            return []

        schedule = spaced_repetition_service.schedule_review_queue(
            user_id=weak_topics[0].get("user_id", settings.DEFAULT_USER_ID)
            if "user_id" in weak_topics[0]
            else settings.DEFAULT_USER_ID,
            weak_topics=weak_topics,
        )

        from datetime import datetime, timedelta

        now = datetime.now()
        for item in schedule:
            position = item.get("scheduled_position", 1)
            estimated_min = item.get("estimated_review_time_min", 10)
            cumulative_min = sum(
                s.get("estimated_review_time_min", 10)
                for s in schedule
                if s["scheduled_position"] <= position
            )
            item["suggested_time"] = (now + timedelta(minutes=cumulative_min)).isoformat()
            item["day_offset"] = 0

        days_so_far = 0
        cumulative_time = 0
        for item in schedule:
            estimated = item.get("estimated_review_time_min", 10)
            cumulative_time += estimated
            if cumulative_time > 120:
                days_so_far += 1
                cumulative_time = estimated
            item["day_offset"] = days_so_far

        logger.info(f"调度间隔重复: {len(schedule)} 个知识点, 预计 {days_so_far + 1} 天完成")
        return schedule

    @staticmethod
    def _determine_phase_label(topics: list[dict]) -> str:
        weak_count = sum(1 for t in topics if t["status"] == "weak")
        ready_count = sum(1 for t in topics if t["action"] == "learn")
        mastered_count = sum(1 for t in topics if t["status"] == "mastered")

        if weak_count > len(topics) * 0.5:
            return "薄弱知识点强化阶段"
        if ready_count > len(topics) * 0.5:
            return "新知识点学习阶段"
        if mastered_count > len(topics) * 0.5:
            return "已掌握知识巩固阶段"
        return "综合提升阶段"

    async def generate_path(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        return await self.process(ctx, stream)

    async def adjust_path(self, ctx: UnifiedContext, stream: StreamBus) -> dict:
        ctx.user_message = "根据最新学习情况，调整我的学习路径"
        return await self.process(ctx, stream)
