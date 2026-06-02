# -*- coding: utf-8 -*-
"""资源生成子 Agent 包。"""
from agents.resource_subagents.lecture import LectureAgent       # noqa: F401
from agents.resource_subagents.quiz import QuizAgent             # noqa: F401
from agents.resource_subagents.mindmap import MindMapAgent       # noqa: F401
from agents.resource_subagents.code_lab import CodeLabAgent      # noqa: F401
from agents.resource_subagents.reading import ReadingAgent       # noqa: F401
from agents.resource_subagents.animation import AnimationAgent   # noqa: F401
from agents.resource_subagents.ppt import PPTAgent               # noqa: F401

__all__ = [
    "LectureAgent", "QuizAgent", "MindMapAgent", "CodeLabAgent",
    "ReadingAgent", "AnimationAgent", "PPTAgent",
]
