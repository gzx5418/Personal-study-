# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_reading")
class ReadingAgent(ResourceSubAgent):
    _resource_type = "extended_reading"
    _display_name = "拓展阅读生成"
    _prompt_key = "generate_extended_reading"

    def __init__(self) -> None:
        super().__init__(agent_name="reading_agent", capability="gen_reading")
