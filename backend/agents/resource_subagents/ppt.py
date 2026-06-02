# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_ppt")
class PPTAgent(ResourceSubAgent):
    _resource_type = "ppt_outline"
    _display_name = "PPT提纲生成"
    _prompt_key = "generate_ppt_outline"

    def __init__(self) -> None:
        super().__init__(agent_name="ppt_agent", capability="gen_ppt")
