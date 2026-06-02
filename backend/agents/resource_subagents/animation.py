# -*- coding: utf-8 -*-
from core.agent import register_agent
from agents.resource_subagents.base import ResourceSubAgent


@register_agent("gen_animation")
class AnimationAgent(ResourceSubAgent):
    _resource_type = "animation"
    _display_name = "教学动画生成"
    _prompt_key = "generate_animation"

    def __init__(self) -> None:
        super().__init__(agent_name="animation_agent", capability="gen_animation")
