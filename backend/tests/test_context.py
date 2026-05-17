from __future__ import annotations

import time
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.context import UnifiedContext


@pytest.fixture
def context():
    return UnifiedContext(session_id="test_session", user_id="test_user")


@pytest.fixture
def context_with_state():
    ctx = UnifiedContext(session_id="state_session", user_id="state_user")
    ctx.set_state("key1", "value1")
    ctx.set_state("key2", {"nested": "data"})
    return ctx


class TestUnifiedContextInitialization:
    def test_default_initialization(self):
        ctx = UnifiedContext()
        assert ctx.session_id is not None
        assert len(ctx.session_id) == 12
        assert ctx.user_id == "default"
        assert ctx.user_message == ""
        assert ctx.active_capability == "chat"
        assert ctx.history == []
        assert ctx.enabled_tools == []
        assert ctx.knowledge_base_refs == []
        assert ctx.attachments == []
        assert ctx.language == "zh"
        assert ctx.profile_context == {}
        assert ctx.memory_context == {}
        assert ctx.mastery_context == {}
        assert ctx.config_overrides == {}
        assert ctx.metadata == {}
        assert ctx.shared_state == {}
        assert ctx.state_history == []
        assert isinstance(ctx.created_at, float)

    def test_custom_initialization(self, context):
        assert context.session_id == "test_session"
        assert context.user_id == "test_user"


class TestGetStateSetState:
    def test_get_state_existing_key(self, context_with_state):
        assert context_with_state.get_state("key1") == "value1"
        assert context_with_state.get_state("key2") == {"nested": "data"}

    def test_get_state_nonexistent_key(self, context):
        assert context.get_state("nonexistent") is None

    def test_get_state_with_default(self, context):
        assert context.get_state("nonexistent", "default_value") == "default_value"

    def test_set_state(self, context):
        context.set_state("test_key", "test_value")
        assert context.get_state("test_key") == "test_value"
        assert "test_key" in context.shared_state

    def test_set_state_overwrite(self, context):
        context.set_state("key", "old_value")
        context.set_state("key", "new_value")
        assert context.get_state("key") == "new_value"


class TestStateHistory:
    def test_state_history_recorded(self, context):
        context.set_state("key1", "value1")
        context.set_state("key2", "value2")
        assert len(context.state_history) == 2

    def test_state_history_entry_structure(self, context):
        start_time = time.time()
        context.set_state("test_key", "test_value")
        end_time = time.time()

        entry = context.state_history[0]
        assert entry["key"] == "test_key"
        assert entry["value"] == "test_value"
        assert "timestamp" in entry
        assert start_time <= entry["timestamp"] <= end_time

    def test_get_history(self, context):
        context.set_state("key", "value1")
        context.set_state("other", "other_value")
        context.set_state("key", "value2")

        history = context.get_history("key")
        assert len(history) == 2
        assert history[0]["value"] == "value1"
        assert history[1]["value"] == "value2"

    def test_get_history_nonexistent_key(self, context):
        assert context.get_history("nonexistent") == []


class TestToDictFromDict:
    def test_to_dict(self, context):
        context.user_message = "hello"
        context.set_state("test", 123)

        data = context.to_dict()
        assert data["session_id"] == "test_session"
        assert data["user_id"] == "test_user"
        assert data["user_message"] == "hello"
        assert data["shared_state"]["test"] == 123
        assert "created_at" in data

    def test_from_dict(self):
        data = {
            "session_id": "restored_session",
            "user_id": "restored_user",
            "user_message": "restored_message",
            "active_capability": "diagnostic",
            "language": "en",
            "shared_state": {"key": "value"},
        }
        ctx = UnifiedContext.from_dict(data)
        assert ctx.session_id == "restored_session"
        assert ctx.user_id == "restored_user"
        assert ctx.user_message == "restored_message"
        assert ctx.active_capability == "diagnostic"
        assert ctx.language == "en"
        assert ctx.get_state("key") == "value"

    def test_from_dict_ignores_unknown_keys(self):
        data = {
            "session_id": "test",
            "unknown_field": "should_be_ignored",
        }
        ctx = UnifiedContext.from_dict(data)
        assert ctx.session_id == "test"
        assert not hasattr(ctx, "unknown_field") or ctx.unknown_field != "should_be_ignored"

    def test_roundtrip(self, context):
        context.set_state("roundtrip_key", [1, 2, 3])
        data = context.to_dict()
        restored = UnifiedContext.from_dict(data)
        assert restored.session_id == context.session_id
        assert restored.get_state("roundtrip_key") == [1, 2, 3]


class TestMerge:
    def test_merge_shared_state(self, context):
        context.set_state("local_key", "local_value")

        other = UnifiedContext()
        other.set_state("other_key", "other_value")

        context.merge(other)
        assert context.get_state("local_key") == "local_value"
        assert context.get_state("other_key") == "other_value"

    def test_merge_overwrites_existing(self, context):
        context.set_state("shared_key", "local_value")

        other = UnifiedContext()
        other.set_state("shared_key", "other_value")

        context.merge(other)
        assert context.get_state("shared_key") == "other_value"

    def test_merge_state_history(self, context):
        context.set_state("key1", "value1")

        other = UnifiedContext()
        other.set_state("key2", "value2")
        other.set_state("key3", "value3")

        original_len = len(context.state_history)
        context.merge(other)
        assert len(context.state_history) == original_len + 2
