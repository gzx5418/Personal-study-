# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_mindmap")
class MindMapAgent(ResourceSubAgent):
    _resource_type = "mindmap"
    _display_name = "思维导图生成"
    _prompt_key = "generate_mindmap"

    def __init__(self) -> None:
        super().__init__(agent_name="mindmap_agent", capability="gen_mindmap")
