from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """创建测试客户端。"""
    os.environ.setdefault("LLM_API_KEY", "test-key")
    os.environ.setdefault("LLM_HOST", "https://api.siliconflow.cn/v1")
    os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing")
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "智学助手"
        assert data["status"] == "running"

    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_config(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200
        data = r.json()
        assert "app_name" in data

    def test_courses(self, client):
        r = client.get("/api/courses")
        assert r.status_code == 200
        data = r.json()
        assert "courses" in data


class TestAuthEndpoints:
    def test_register(self, client):
        import time
        uid = f"reg_{int(time.time() * 1000)}"
        r = client.post("/api/auth/register", json={
            "user_id": uid,
            "password": "pass1234",
            "name": "API测试",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == uid
        assert "token" in data

    def test_login(self, client):
        client.post("/api/auth/register", json={
            "user_id": "api_test_login",
            "password": "pass1234",
        })
        r = client.post("/api/auth/login", json={
            "user_id": "api_test_login",
            "password": "pass1234",
        })
        assert r.status_code == 200
        assert "token" in r.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "user_id": "api_test_wrong",
            "password": "correct",
        })
        r = client.post("/api/auth/login", json={
            "user_id": "api_test_wrong",
            "password": "wrong",
        })
        assert r.status_code == 401


class TestProfileEndpoints:
    def test_get_profile(self, client):
        r = client.get("/api/profile/api_test_user")
        assert r.status_code == 200
        data = r.json()
        assert "major_or_background" in data

    def test_update_profile(self, client):
        r = client.put("/api/profile/api_test_user", json={
            "updates": {"major_or_background": "计算机"}
        })
        assert r.status_code == 200

    @pytest.mark.skip(reason="依赖 agent 注册，测试环境中未初始化")
    def test_check_profile(self, client):
        r = client.get("/api/profile/check/api_test_user")
        assert r.status_code == 200


class TestEvaluationEndpoints:
    def test_mastery(self, client):
        r = client.get("/api/evaluation/mastery/api_test_user")
        assert r.status_code == 200
        data = r.json()
        assert "mastery" in data
        assert "summary" in data


class TestLearningPathEndpoints:
    def test_timeline(self, client):
        r = client.get("/api/learning-path/timeline/api_test_user")
        assert r.status_code == 200
        data = r.json()
        assert "phases" in data
        assert "total_nodes" in data

    def test_graph(self, client):
        r = client.get("/api/learning-path/graph/api_test_user")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data

    def test_spaced_repetition(self, client):
        r = client.get("/api/learning-path/spaced-repetition/api_test_user")
        assert r.status_code == 200
        data = r.json()
        assert "due_reviews" in data


class TestKnowledgeEndpoints:
    def test_list_knowledge(self, client):
        r = client.get("/api/knowledge/list")
        assert r.status_code == 200
        assert "knowledge_bases" in r.json()

    def test_versions(self, client):
        r = client.get("/api/knowledge/python_programming/versions")
        assert r.status_code == 200


class TestPathEndpoints:
    def test_graph(self, client):
        r = client.get("/api/path/graph/python_programming")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data


class TestResourceEndpoints:
    def test_list_resources(self, client):
        r = client.get("/api/resources/list/api_test_user")
        assert r.status_code == 200
        assert "resources" in r.json()


class TestChatEndpoints:
    def test_list_sessions(self, client):
        r = client.get("/api/chat/sessions/api_test_user")
        assert r.status_code == 200
        assert "sessions" in r.json()


class TestStatsEndpoints:
    def test_stats(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        assert "token_stats" in r.json()
