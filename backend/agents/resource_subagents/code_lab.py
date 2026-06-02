# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_code_lab")
class CodeLabAgent(ResourceSubAgent):
    _resource_type = "code_lab"
    _display_name = "代码实操案例生成"
    _prompt_key = "generate_code_lab"

    def __init__(self) -> None:
        super().__init__(agent_name="code_lab_agent", capability="gen_code_lab")
