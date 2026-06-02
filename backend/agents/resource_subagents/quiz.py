# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_quiz")
class QuizAgent(ResourceSubAgent):
    _resource_type = "quiz"
    _display_name = "练习题生成"
    _prompt_key = "generate_quiz"

    def __init__(self) -> None:
        super().__init__(agent_name="quiz_agent", capability="gen_quiz")
