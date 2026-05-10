from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UnifiedContext:
    """贯穿整个系统的统一上下文，参考 DeepTutor UnifiedContext 设计。"""

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
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_message": self.user_message,
            "active_capability": self.active_capability,
            "language": self.language,
            "profile_context": self.profile_context,
            "mastery_context": self.mastery_context,
        }
