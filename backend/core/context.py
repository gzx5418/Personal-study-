from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UnifiedContext:
    """贯穿整个系统的统一上下文。"""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_id: str = "default"
    user_message: str = ""
    active_capability: str = "chat"

    history: list[dict[str, str]] = field(default_factory=list)
    enabled_tools: list[str] = field(default_factory=list)
    knowledge_base_refs: list[str] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)
    language: str = "zh"

    profile_context: dict[str, Any] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)
    mastery_context: dict[str, Any] = field(default_factory=dict)

    config_overrides: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)
    state_history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_message": self.user_message,
            "active_capability": self.active_capability,
            "history": self.history,
            "enabled_tools": self.enabled_tools,
            "knowledge_base_refs": self.knowledge_base_refs,
            "attachments": self.attachments,
            "language": self.language,
            "profile_context": self.profile_context,
            "memory_context": self.memory_context,
            "mastery_context": self.mastery_context,
            "config_overrides": self.config_overrides,
            "metadata": self.metadata,
            "shared_state": self.shared_state,
            "state_history": self.state_history,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UnifiedContext:
        context = cls()
        for key, value in data.items():
            if hasattr(context, key):
                setattr(context, key, value)
        return context

    def get_state(self, key: str, default=None) -> Any:
        return self.shared_state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self.shared_state[key] = value
        self.state_history.append({
            "key": key,
            "value": value,
            "timestamp": time.time(),
        })

    def merge(self, other: UnifiedContext) -> None:
        self.shared_state.update(other.shared_state)
        self.state_history.extend(other.state_history)

    def get_history(self, key: str) -> list:
        return [entry for entry in self.state_history if entry.get("key") == key]
