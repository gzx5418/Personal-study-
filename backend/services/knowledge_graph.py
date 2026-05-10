from __future__ import annotations

import json
import os
from typing import Any

import networkx as nx

from config import settings


class KnowledgeGraphService:
    """知识依赖图服务 — 项目核心创新点之一。
    
    管理课程知识点的前置依赖关系（DAG），支持：
    - 查询知识点的前置依赖和后续知识点
    - 基于掌握度计算推荐学习顺序
    - 拓扑排序生成学习路径
    """

    def __init__(self) -> None:
        self._graphs: dict[str, nx.DiGraph] = {}
        self._nodes: dict[str, dict[str, dict]] = {}
        self._load()

    def _load(self) -> None:
        graph_file = os.path.join(settings.KNOWLEDGE_DIR, "knowledge_graph.json")
        if not os.path.exists(graph_file):
            graph_file = os.path.join(os.path.dirname(settings.KNOWLEDGE_DIR), "knowledge_graph.json")
        if os.path.exists(graph_file):
            with open(graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._build_graph(data)

    def _build_graph(self, data: dict) -> None:
        for course_id, course_data in data.items():
            G = nx.DiGraph()
            nodes = {}

            for node in course_data.get("nodes", []):
                node_id = node["id"]
                G.add_node(node_id, **node)
                nodes[node_id] = node

            for edge in course_data.get("edges", []):
                G.add_edge(edge["from"], edge["to"])

            self._graphs[course_id] = G
            self._nodes[course_id] = nodes

    def load_course_data(self, course_id: str, data: dict) -> None:
        graph_file = os.path.join(settings.KNOWLEDGE_DIR, "knowledge_graph.json")
        existing = {}
        if os.path.exists(graph_file):
            with open(graph_file, "r", encoding="utf-8") as f:
                existing = json.load(f)

        existing[course_id] = data
        os.makedirs(os.path.dirname(graph_file), exist_ok=True)
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        self._build_graph(existing)

    def get_graph(self, course_id: str) -> nx.DiGraph | None:
        return self._graphs.get(course_id)

    def get_node(self, course_id: str, node_id: str) -> dict | None:
        return self._nodes.get(course_id, {}).get(node_id)

    def get_all_nodes(self, course_id: str) -> list[dict]:
        return list(self._nodes.get(course_id, {}).values())

    def get_prerequisites(self, course_id: str, node_id: str) -> list[str]:
        G = self._graphs.get(course_id)
        if G is None:
            return []
        return list(G.predecessors(node_id))

    def get_dependents(self, course_id: str, node_id: str) -> list[str]:
        G = self._graphs.get(course_id)
        if G is None:
            return []
        return list(G.successors(node_id))

    def get_learning_path(
        self,
        course_id: str,
        mastery: dict[str, dict] | None = None,
        target_nodes: list[str] | None = None,
    ) -> list[dict]:
        """基于拓扑排序和掌握度生成个性化学习路径。"""
        G = self._graphs.get(course_id)
        if G is None:
            return []

        if target_nodes:
            subgraph_nodes = set()
            for tn in target_nodes:
                subgraph_nodes.add(tn)
                subgraph_nodes.update(nx.ancestors(G, tn))
            subG = G.subgraph(subgraph_nodes).copy()
        else:
            subG = G

        topo_order = list(nx.topological_sort(subG))
        path = []
        mastery = mastery or {}

        for node_id in topo_order:
            node_data = dict(subG.nodes[node_id])
            prereqs = list(subG.predecessors(node_id))
            prereq_met = all(
                mastery.get(p, {}).get("level", 0) >= 0.5 for p in prereqs
            )
            current_mastery = mastery.get(node_id, {}).get("level", 0)

            if current_mastery >= 0.8:
                status = "mastered"
            elif current_mastery >= 0.5:
                status = "in_progress"
            elif prereq_met:
                status = "ready"
            else:
                status = "blocked"

            path.append({
                "id": node_id,
                "name": node_data.get("name", node_id),
                "difficulty": node_data.get("difficulty", 1),
                "chapter": node_data.get("chapter", ""),
                "prerequisites": prereqs,
                "prereq_met": prereq_met,
                "mastery_level": current_mastery,
                "status": status,
            })

        return path

    def get_recommended_next(
        self,
        course_id: str,
        mastery: dict[str, dict],
        limit: int = 5,
    ) -> list[dict]:
        path = self.get_learning_path(course_id, mastery)
        ready = [n for n in path if n["status"] in ("ready", "in_progress")]
        ready.sort(key=lambda x: (x["difficulty"], -x["mastery_level"]))
        return ready[:limit]

    def get_chapters(self, course_id: str) -> dict[str, list[dict]]:
        nodes = self.get_all_nodes(course_id)
        chapters: dict[str, list[dict]] = {}
        for node in nodes:
            ch = node.get("chapter", "未分类")
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(node)
        return chapters


knowledge_graph_service = KnowledgeGraphService()
