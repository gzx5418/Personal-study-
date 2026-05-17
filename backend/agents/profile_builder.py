from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus

PROFILE_DIMENSIONS = [
    {"phase": "background", "field": "major_or_background", "progress": "1/8",
     "question": "你好！我是你的智学助手 😊 为了给你量身定制学习计划，我需要先了解一下你的情况。\n\n**第一个问题：你是哪个专业的？现在大几？**\n\n  1. 计算机相关专业（大一/大二）\n  2. 理工科专业（如电子、自动化等）\n  3. 文科或商科专业\n  4. 其他专业或已经工作"},
    {"phase": "goal", "field": "learning_goal", "progress": "2/8",
     "question": "很好！接下来...\n\n**你学习Python的主要目标是什么？**\n\n  1. 课程要求，需要通过考试\n  2. 想做数据分析或人工智能\n  3. 想做网站或小工具\n  4. 纯兴趣，想学编程"},
    {"phase": "basis", "field": "knowledge_level", "progress": "3/8",
     "question": "了解了！那我们看看你的基础...\n\n**你之前有编程经验吗？**\n\n  1. 完全零基础，从未接触过\n  2. 看过一些教程，但不熟练\n  3. 学过一点，能写简单程序\n  4. 有其他语言基础（如C/Java）"},
    {"phase": "style", "field": "learning_style", "progress": "4/8",
     "question": "每个人都有自己喜欢的学习方式...\n\n**你更喜欢哪种学习方式？**\n\n  1. 看视频教程，跟着操作\n  2. 阅读文章/书籍，自己理解\n  3. 直接动手写代码，边做边学\n  4. 先学理论，再实践"},
    {"phase": "weakness", "field": "weak_points", "progress": "5/8",
     "question": "了解！说说你的担心...\n\n**你觉得学习编程时，哪方面最容易卡住？**\n\n  1. 逻辑思维，不知道怎么把想法变成代码\n  2. 语法记不住，总是写错\n  3. 调试报错，看不懂错误信息\n  4. 缺乏项目经验，不知道学完能做什么"},
    {"phase": "time", "field": "time_budget", "progress": "6/8",
     "question": "时间安排很重要！\n\n**你每天大概能花多少时间学习Python？**\n\n  1. 不到30分钟（碎片时间）\n  2. 30分钟到1小时\n  3. 1-2小时\n  4. 2小时以上（深入学习）"},
    {"phase": "pace", "field": "pace_preference", "progress": "7/8",
     "question": "了解你的节奏偏好...\n\n**你希望以什么节奏学习？**\n\n  1. 慢节奏，每个知识点都彻底理解\n  2. 正常节奏，稳扎稳打\n  3. 快节奏，重点突破核心内容\n  4. 灵活节奏，根据内容难度调整"},
    {"phase": "schedule", "field": "modality_preference", "progress": "8/8",
     "question": "最后一个问题！🎉\n\n**你更喜欢哪种练习方式？**\n\n  1. 选择题为主，快速检验\n  2. 编程题为主，动手实践\n  3. 项目驱动，做完整小项目\n  4. 混合方式，多种题型结合"},
]


@register_agent("profile_build")
class ProfileBuilderAgent(BaseAgent):
    """画像引导 Agent — 通过对话式问答构建学生画像。"""

    def __init__(self) -> None:
        super().__init__(agent_name="profile_builder", module_name="profile")

    def _get_next_dimension(self, profile: dict) -> dict | None:
        completed = profile.get("_completed_phases", [])
        for dim in PROFILE_DIMENSIONS:
            if dim["phase"] not in completed:
                return dim
        return None

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("profile_build", "正在引导构建学习画像...")

        from services.profile_service import profile_service
        current_profile = profile_service.get_profile(ctx.user_id)

        completed = current_profile.get("_completed_phases", [])
        user_msgs = [m for m in ctx.history if m["role"] == "user"]

        if len(user_msgs) >= 2:
            current_dim = self._get_next_dimension(current_profile)
            if current_dim:
                last_user_msg = user_msgs[-1]["content"]
                await self._extract_and_save(ctx.user_id, current_profile, current_dim, last_user_msg, ctx.history)
                current_profile = profile_service.get_profile(ctx.user_id)

        next_dim = self._get_next_dimension(current_profile)

        if next_dim is None:
            summary = self._generate_summary(current_profile)
            stream.content(f"画像构建完成！🎉\n\n{summary}")
            result = {"phase": "complete", "summary": summary, "updates": current_profile}
            stream.result(result)
            stream.stage_end("profile_build")
            return result

        question_text = next_dim["question"]
        display = f"{question_text}\n\n[进度: {next_dim['progress']}]"
        stream.content(display)

        result = {"phase": next_dim["phase"], "question": question_text, "progress": next_dim["progress"]}
        stream.result(result)
        stream.stage_end("profile_build")
        return result

    async def _extract_and_save(self, user_id: str, profile: dict, prev_dim: dict,
                                last_user_msg: str, history: list[dict]) -> None:
        from services.profile_service import profile_service

        extract_prompt = (
            f"从学生的回答中提取信息。\n"
            f"要收集的字段：{prev_dim['field']}\n"
            f"学生回答：{last_user_msg}\n"
            f"对话上下文：{json.dumps([{'role':m['role'],'content':m['content'][:100]} for m in history[-6:]], ensure_ascii=False)}\n"
            f"只输出提取到的值（一个简短的字符串），不要输出其他内容。"
            f"如果字段是learning_style或weak_points，输出逗号分隔的标签列表。"
            f"如果字段是modality_preference，输出一个简短标签，如 mixed/code/document/slides。"
        )

        extracted = await self.call_llm([
            {"role": "system", "content": "你是信息提取助手。从用户回答中提取指定字段的值，只输出提取结果。"},
            {"role": "user", "content": extract_prompt},
        ], temperature=0.3)
        extracted = extracted.strip().strip('"').strip("'")

        if prev_dim["field"] in ("learning_style", "weak_points"):
            items = [x.strip() for x in extracted.split(",") if x.strip()]
            profile_service.update_profile(user_id, {prev_dim["field"]: items})
        else:
            profile_service.update_profile(user_id, {prev_dim["field"]: extracted})

        completed = list(profile.get("_completed_phases", []))
        if prev_dim["phase"] not in completed:
            completed.append(prev_dim["phase"])
        profile_service.update_profile(user_id, {"_completed_phases": completed})

    def _generate_summary(self, profile: dict) -> str:
        from services.profile_service import profile_service
        parts = []
        if profile_service.get_field_value(profile, "major_or_background"):
            parts.append(f"- 专业背景：{profile_service.get_field_value(profile, 'major_or_background')}")
        if profile_service.get_field_value(profile, "learning_goal"):
            parts.append(f"- 学习目标：{profile_service.get_field_value(profile, 'learning_goal')}")
        if profile_service.get_field_value(profile, "knowledge_level"):
            parts.append(f"- 知识水平：{profile_service.get_field_value(profile, 'knowledge_level')}")
        learning_style = profile_service.get_field_value(profile, "learning_style", [])
        if learning_style:
            parts.append(f"- 学习风格：{', '.join(learning_style)}")
        weak_points = profile_service.get_field_value(profile, "weak_points", [])
        if weak_points:
            parts.append(f"- 薄弱环节：{', '.join(weak_points)}")
        if profile_service.get_field_value(profile, "time_budget"):
            parts.append(f"- 时间预算：{profile_service.get_field_value(profile, 'time_budget')}")
        if profile_service.get_field_value(profile, "pace_preference"):
            parts.append(f"- 学习节奏：{profile_service.get_field_value(profile, 'pace_preference')}")
        prefs = profile.get("preferences", {})
        if isinstance(prefs, dict) and prefs:
            parts.append(f"- 偏好：{json.dumps(prefs, ensure_ascii=False)}")
        return "\n".join(parts)

    async def check_and_start(self, user_id: str) -> dict:
        from services.profile_service import profile_service
        profile = profile_service.get_profile(user_id)
        needs_build = (
            not profile_service.get_field_value(profile, "major_or_background")
            and not profile_service.get_field_value(profile, "learning_goal")
            and not profile_service.get_field_value(profile, "learning_style")
        )
        return {"needs_build": needs_build, "profile": profile}
