from __future__ import annotations

import os
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).parent.parent / "prompts"


class PromptManager:
    """提示词管理器。
    
    从 prompts/ 目录加载提示词模板。
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def get_prompt(self, module: str, name: str, language: str = "zh") -> str:
        cache_key = f"{module}:{name}:{language}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        path = PROMPT_DIR / module / f"{name}_{language}.txt"
        if not path.exists():
            path = PROMPT_DIR / module / f"{name}.txt"
        if not path.exists():
            return ""

        content = path.read_text(encoding="utf-8").strip()
        self._cache[cache_key] = content
        return content

    def reload(self) -> None:
        self._cache.clear()


prompt_manager = PromptManager()
