from __future__ import annotations

import json
import os
import time
from unittest.mock import patch

import pytest


@pytest.fixture
def profile_service(tmp_path):
    """创建使用内存存储的 ProfileService 实例。"""
    profile_file = str(tmp_path / "profiles.json")
    with patch("services.profile_service.settings") as mock_settings:
        mock_settings.PROFILE_FILE = profile_file
        from services.profile_service import ProfileService
        svc = ProfileService()
        svc._use_db = False
        svc._db = None
        svc._profiles = {}
        yield svc


class TestGetProfile:
    def test_creates_default_profile(self, profile_service):
        profile = profile_service.get_profile("new_user")
        assert "major_or_background" in profile
        assert "learning_goal" in profile
        assert "knowledge_level" in profile
        assert profile["major_or_background"]["value"] == ""
        assert profile["created_at"] is not None

    def test_returns_existing_profile(self, profile_service):
        profile_service.update_profile("user1", {"major_or_background": "计算机"})
        profile = profile_service.get_profile("user1")
        assert profile["major_or_background"]["value"] == "计算机"


class TestUpdateProfile:
    def test_update_simple_field(self, profile_service):
        profile_service.update_profile("user1", {"major_or_background": "计算机科学"})
        profile = profile_service.get_profile("user1")
        assert profile["major_or_background"]["value"] == "计算机科学"
        assert profile["major_or_background"]["confidence"] > 0

    def test_update_learning_goal(self, profile_service):
        profile_service.update_profile("user1", {"learning_goal": "学Python"})
        profile = profile_service.get_profile("user1")
        assert profile["learning_goal"]["value"] == "学Python"

    def test_update_list_field(self, profile_service):
        profile_service.update_profile("user1", {"weak_points": ["循环", "函数"]})
        profile = profile_service.get_profile("user1")
        assert profile["weak_points"]["value"] == ["循环", "函数"]

    def test_update_preserves_other_fields(self, profile_service):
        profile_service.update_profile("user1", {"major_or_background": "计算机"})
        profile_service.update_profile("user1", {"learning_goal": "AI"})
        profile = profile_service.get_profile("user1")
        assert profile["major_or_background"]["value"] == "计算机"
        assert profile["learning_goal"]["value"] == "AI"

    def test_update_sets_timestamp(self, profile_service):
        profile_service.update_profile("user1", {"major_or_background": "CS"})
        profile = profile_service.get_profile("user1")
        assert profile["updated_at"] is not None
        assert profile["updated_at"] > 0


class TestGetFieldValue:
    def test_get_structured_field(self, profile_service):
        profile = profile_service.get_profile("user1")
        profile["major_or_background"] = {"value": "物理", "confidence": 0.8, "evidence": [], "updated_at": None}
        val = profile_service.get_field_value(profile, "major_or_background")
        assert val == "物理"

    def test_get_missing_field(self, profile_service):
        profile = profile_service.get_profile("user1")
        val = profile_service.get_field_value(profile, "nonexistent")
        assert val == ""

    def test_get_with_default(self, profile_service):
        profile = profile_service.get_profile("user1")
        val = profile_service.get_field_value(profile, "nonexistent", default="默认")
        assert val == "默认"


class TestNormalizeProfile:
    def test_normalize_creates_structured_fields(self, profile_service):
        profile = {"major_or_background": "测试"}
        normalized = profile_service._normalize_profile(profile)
        assert isinstance(normalized["major_or_background"], dict)
        assert "value" in normalized["major_or_background"]
        assert "confidence" in normalized["major_or_background"]

    def test_normalize_preserves_existing_structure(self, profile_service):
        profile = {
            "major_or_background": {"value": "CS", "confidence": 0.9, "evidence": ["test"], "updated_at": None}
        }
        normalized = profile_service._normalize_profile(profile)
        assert normalized["major_or_background"]["value"] == "CS"
        assert normalized["major_or_background"]["confidence"] == 0.9


class TestAddWeakPoint:
    def test_add_new_weak_point(self, profile_service):
        profile_service.add_weak_point("user1", "循环")
        profile = profile_service.get_profile("user1")
        assert "循环" in profile["weak_points"]["value"]

    def test_add_duplicate_weak_point(self, profile_service):
        profile_service.add_weak_point("user1", "循环")
        profile_service.add_weak_point("user1", "循环")
        profile = profile_service.get_profile("user1")
        assert profile["weak_points"]["value"].count("循环") == 1


class TestProfileContextText:
    def test_returns_context_text(self, profile_service):
        profile_service.update_profile("user1", {"major_or_background": "计算机"})
        text = profile_service.get_profile_context_text("user1")
        assert "计算机" in text

    def test_empty_profile_returns_empty(self, profile_service):
        text = profile_service.get_profile_context_text("empty_user")
        assert text == "" or len(text) < 50
