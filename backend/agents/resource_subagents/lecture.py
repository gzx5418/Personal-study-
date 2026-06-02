# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_lecture")
class LectureAgent(ResourceSubAgent):
    _resource_type = "lecture"
    _display_name = "讲义生成"
    _prompt_key = "generate_lecture"

    def __init__(self) -> None:
        super().__init__(agent_name="lecture_agent", capability="gen_lecture")
