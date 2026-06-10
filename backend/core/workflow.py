from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger("zhixue.workflow")


@dataclass
class WorkflowNode:
    name: str
    handler: Callable[[WorkflowState], Awaitable[dict[str, Any]]]
    next_nodes: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    source: str
    target: str
    condition: Callable[[WorkflowState], bool] | None = None


@dataclass
class WorkflowState:
    current_node: str
    data: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    is_finished: bool = False


class Workflow:
    def __init__(self, name: str) -> None:
        self.name = name
        self.nodes: dict[str, WorkflowNode] = {}
        self.edges: list[WorkflowEdge] = []
        self.entry_node: str = ""

    def add_node(
        self,
        name: str,
        handler: Callable[[WorkflowState], Awaitable[dict[str, Any]]],
    ) -> None:
        node = WorkflowNode(name=name, handler=handler)
        self.nodes[name] = node

    def add_edge(
        self,
        source: str,
        target: str,
        condition: Callable[[WorkflowState], bool] | None = None,
    ) -> None:
        edge = WorkflowEdge(source=source, target=target, condition=condition)
        self.edges.append(edge)

    def set_entry(self, name: str) -> None:
        if name not in self.nodes:
            raise ValueError(f"节点 '{name}' 不存在")
        self.entry_node = name

    def _resolve_next(self, state: WorkflowState) -> str | None:
        current = self.nodes.get(state.current_node)
        if not current:
            return None

        for key, target in current.next_nodes.items():
            if state.data.get(key):
                return target

        for edge in self.edges:
            if edge.source != state.current_node:
                continue
            if edge.condition is None:
                return edge.target
            if edge.condition(state):
                return edge.target

        return None

    async def run(self, initial_data: dict[str, Any] | None = None) -> WorkflowState:
        if not self.entry_node:
            raise ValueError(f"工作流 '{self.name}' 未设置入口节点")

        state = WorkflowState(
            current_node=self.entry_node,
            data=dict(initial_data) if initial_data else {},
        )

        max_steps = 50
        step_count = 0

        while not state.is_finished and step_count < max_steps:
            node = self.nodes.get(state.current_node)
            if not node:
                logger.error(f"节点 '{state.current_node}' 不存在，工作流终止")
                state.is_finished = True
                break

            logger.info(f"[{self.name}] 执行节点: {node.name} (步骤 {step_count + 1})")

            try:
                updates = await node.handler(state)
                if updates:
                    state.data.update(updates)
            except Exception as e:
                logger.error(f"节点 '{node.name}' 执行失败: {e}", exc_info=True)
                state.data["_error"] = str(e)
                state.is_finished = True
                break

            state.history.append({
                "node": node.name,
                "step": step_count + 1,
                "data_keys": list(state.data.keys()),
            })

            next_node = self._resolve_next(state)
            if next_node is None:
                state.is_finished = True
            else:
                state.current_node = next_node

            step_count += 1

        if step_count >= max_steps:
            logger.warning(f"工作流 '{self.name}' 达到最大步数 {max_steps}，强制终止")
            state.is_finished = True

        return state


class WorkflowEngine:
    _instance: WorkflowEngine | None = None
    _lock = threading.Lock()

    def __new__(cls) -> WorkflowEngine:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.workflows = {}
            return cls._instance

    def register(self, workflow: Workflow) -> None:
        self.workflows[workflow.name] = workflow
        logger.info(f"注册工作流: {workflow.name}")

    async def execute(
        self,
        name: str,
        initial_data: dict[str, Any] | None = None,
    ) -> WorkflowState:
        workflow = self.workflows.get(name)
        if not workflow:
            raise ValueError(f"工作流 '{name}' 未注册")
        return await workflow.run(initial_data)


workflow_engine = WorkflowEngine()


def create_deep_solve_workflow() -> Workflow:
    from services.llm_service import llm_service

    workflow = Workflow("deep_solve")

    async def plan_node(state: WorkflowState) -> dict[str, Any]:
        question = state.data.get("question", "")
        messages = [
            {
                "role": "system",
                "content": "你是一个求解规划专家。请为以下问题制定一个包含多个步骤的求解计划。"
                           "返回 JSON 格式：{\"steps\": [{\"id\": 1, \"goal\": \"...\"}, ...]}",
            },
            {"role": "user", "content": question},
        ]
        result_text = await llm_service.chat(messages, temperature=0.3, response_format={"type": "json_object"})
        from utils import safe_json_parse
        result = safe_json_parse(result_text, default={"steps": []})
        return {"plan": result}

    async def solve_node(state: WorkflowState) -> dict[str, Any]:
        question = state.data.get("question", "")
        plan = state.data.get("plan", {})
        steps = plan.get("steps", [])
        step_results: list[dict[str, Any]] = []
        previous_knowledge = ""

        for i, step in enumerate(steps):
            messages = [
                {
                    "role": "system",
                    "content": "你是一个逐步求解专家。请根据以下信息完成当前步骤的求解。"
                               f"问题：{question}\n"
                               f"计划：{plan}\n"
                               f"当前步骤：{step}\n"
                               f"已有知识：{previous_knowledge or '无'}",
                },
                {"role": "user", "content": f"请完成步骤 {step.get('id', i + 1)}：{step.get('goal', '')}"},
            ]
            result_text = await llm_service.chat(messages, temperature=0.4, response_format={"type": "json_object"})
            from utils import safe_json_parse
            result = safe_json_parse(result_text, default={})
            step_result = {
                "step_id": step.get("id", f"S{i + 1}"),
                "goal": step.get("goal", ""),
                "answer": result.get("step_answer", ""),
            }
            step_results.append(step_result)
            if step_result["answer"]:
                previous_knowledge += f"\n- {step.get('goal', '')}: {step_result['answer']}"

        return {"step_results": step_results}

    async def write_node(state: WorkflowState) -> dict[str, Any]:
        question = state.data.get("question", "")
        plan = state.data.get("plan", {})
        step_results = state.data.get("step_results", [])
        step_results_text = "\n".join(
            f"### {r['step_id']}: {r['goal']}\n{r['answer']}"
            for r in step_results
        )
        messages = [
            {
                "role": "system",
                "content": "你是一个答案撰写专家。请根据以下求解过程，撰写最终的完整答案。"
                           f"问题：{question}\n"
                           f"计划：{plan}\n"
                           f"求解结果：\n{step_results_text}",
            },
            {"role": "user", "content": "请撰写最终的完整答案。"},
        ]
        response = await llm_service.chat(messages, temperature=0.7, max_tokens=3000)
        return {"response": response}

    workflow.add_node("plan", plan_node)
    workflow.add_node("solve", solve_node)
    workflow.add_node("write", write_node)
    workflow.add_edge("plan", "solve")
    workflow.add_edge("solve", "write")
    workflow.set_entry("plan")

    return workflow
