from __future__ import annotations

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.workflow import WorkflowNode, WorkflowEdge, WorkflowState, Workflow


@pytest.fixture
def sample_handler():
    async def handler(state: WorkflowState) -> dict:
        return {"result": "ok"}
    return handler


@pytest.fixture
def workflow():
    return Workflow("test_workflow")


class TestWorkflowNode:
    def test_create_workflow_node(self, sample_handler):
        node = WorkflowNode(name="test_node", handler=sample_handler)
        assert node.name == "test_node"
        assert node.handler == sample_handler
        assert node.next_nodes == {}

    def test_create_workflow_node_with_next_nodes(self, sample_handler):
        next_nodes = {"key1": "node1", "key2": "node2"}
        node = WorkflowNode(name="test_node", handler=sample_handler, next_nodes=next_nodes)
        assert node.next_nodes == next_nodes


class TestWorkflowEdge:
    def test_create_workflow_edge(self):
        edge = WorkflowEdge(source="node1", target="node2")
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.condition is None

    def test_create_workflow_edge_with_condition(self):
        def condition(state: WorkflowState) -> bool:
            return state.data.get("proceed", False)
        edge = WorkflowEdge(source="node1", target="node2", condition=condition)
        assert edge.condition == condition


class TestWorkflow:
    def test_add_node(self, workflow, sample_handler):
        workflow.add_node("node1", sample_handler)
        assert "node1" in workflow.nodes
        assert isinstance(workflow.nodes["node1"], WorkflowNode)
        assert workflow.nodes["node1"].name == "node1"

    def test_add_edge(self, workflow):
        workflow.add_edge("node1", "node2")
        assert len(workflow.edges) == 1
        assert workflow.edges[0].source == "node1"
        assert workflow.edges[0].target == "node2"

    def test_add_edge_with_condition(self, workflow):
        def condition(state: WorkflowState) -> bool:
            return True
        workflow.add_edge("node1", "node2", condition=condition)
        assert workflow.edges[0].condition == condition

    def test_set_entry(self, workflow, sample_handler):
        workflow.add_node("node1", sample_handler)
        workflow.set_entry("node1")
        assert workflow.entry_node == "node1"

    def test_set_entry_nonexistent_node(self, workflow):
        with pytest.raises(ValueError, match="节点 'nonexistent' 不存在"):
            workflow.set_entry("nonexistent")


class TestWorkflowState:
    def test_initialization(self):
        state = WorkflowState(current_node="start")
        assert state.current_node == "start"
        assert state.data == {}
        assert state.history == []
        assert state.is_finished is False

    def test_initialization_with_data(self):
        data = {"key": "value"}
        state = WorkflowState(current_node="start", data=data)
        assert state.data == data


class TestWorkflowExecution:
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, workflow):
        call_count = 0

        async def node1_handler(state: WorkflowState) -> dict:
            nonlocal call_count
            call_count += 1
            return {"node1_result": "done"}

        async def node2_handler(state: WorkflowState) -> dict:
            nonlocal call_count
            call_count += 1
            state.is_finished = True
            return {"node2_result": "done"}

        workflow.add_node("node1", node1_handler)
        workflow.add_node("node2", node2_handler)
        workflow.add_edge("node1", "node2")
        workflow.set_entry("node1")

        result = await workflow.run()
        assert result.is_finished is True
        assert result.current_node == "node2"
        assert call_count == 2
        assert "node1_result" in result.data
        assert "node2_result" in result.data
        assert len(result.history) == 2

    @pytest.mark.asyncio
    async def test_workflow_with_initial_data(self, workflow):
        async def handler(state: WorkflowState) -> dict:
            return {"processed": state.data["input"]}

        workflow.add_node("start", handler)
        workflow.set_entry("start")

        result = await workflow.run(initial_data={"input": "test_data"})
        assert result.data["processed"] == "test_data"

    @pytest.mark.asyncio
    async def test_workflow_with_condition(self, workflow):
        async def start_handler(state: WorkflowState) -> dict:
            return {"proceed": True}

        async def end_handler(state: WorkflowState) -> dict:
            return {"final": True}

        workflow.add_node("start", start_handler)
        workflow.add_node("end", end_handler)

        def condition(state: WorkflowState) -> bool:
            return state.data.get("proceed", False)

        workflow.add_edge("start", "end", condition=condition)
        workflow.set_entry("start")

        result = await workflow.run()
        assert result.is_finished is True
        assert "final" in result.data

    @pytest.mark.asyncio
    async def test_workflow_handler_error(self, workflow):
        async def error_handler(state: WorkflowState) -> dict:
            raise ValueError("test error")

        workflow.add_node("error_node", error_handler)
        workflow.set_entry("error_node")

        result = await workflow.run()
        assert result.is_finished is True
        assert "_error" in result.data
        assert "test error" in result.data["_error"]

    @pytest.mark.asyncio
    async def test_workflow_no_entry(self, workflow):
        with pytest.raises(ValueError, match="未设置入口节点"):
            await workflow.run()
