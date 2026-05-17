from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus


class DeepSolveAgent(BaseAgent):
    """Plan -> Solve -> Write pipeline for complex reasoning tasks."""

    DEEP_MODEL = "deepseek-ai/DeepSeek-V3.2"

    def __init__(self) -> None:
        super().__init__(agent_name="deep_solve_agent", module_name="solve")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        deep_model = ctx.config_overrides.get("reasoning_model") or self.DEEP_MODEL
        stream.stage_start("deep_solve", "正在分析问题...")

        from services.profile_service import profile_service
        from services.mastery_service import mastery_service

        mastery = mastery_service.get_user_mastery(ctx.user_id)
        profile_text = profile_service.get_profile_context_text(ctx.user_id)

        stream.stage_start("plan", "正在制定求解计划...")
        plan = await self._plan(ctx.user_message, profile_text, mastery, stream, deep_model)
        stream.stage_end("plan")

        stream.stage_start("solve", "正在逐步求解...")
        step_results = await self._solve(ctx.user_message, plan, stream, deep_model)
        stream.stage_end("solve")

        stream.stage_start("write", "正在撰写答案...")
        final_answer = await self._write(ctx.user_message, plan, step_results, profile_text, stream, deep_model)
        stream.stage_end("write")

        stream.stage_end("deep_solve")
        return {
            "plan": plan,
            "step_results": step_results,
            "response": final_answer,
        }

    async def _plan(
        self,
        question: str,
        profile_text: str,
        mastery: dict,
        stream: StreamBus,
        deep_model: str,
    ) -> dict:
        prompt = self.load_prompt("plan", {
            "profile": profile_text or "暂无画像信息",
            "mastery": json.dumps(mastery, ensure_ascii=False, indent=2),
            "question": question,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请为以下问题制定求解计划：{question}"},
        ]

        result = await self.call_llm_json(messages, temperature=0.3, model=deep_model)
        stream.thinking(f"求解计划：{len(result.get('steps', []))} 个步骤")
        return result

    async def _solve(
        self,
        question: str,
        plan: dict,
        stream: StreamBus,
        deep_model: str,
    ) -> list[dict]:
        steps = plan.get("steps", [])
        step_results: list[dict] = []
        previous_knowledge = ""

        for i, step in enumerate(steps):
            stream.progress(i + 1, len(steps), f"正在求解步骤 {step.get('id', i + 1)}")
            step_history = json.dumps(step_results[-3:], ensure_ascii=False) if step_results else "无"

            prompt = self.load_prompt("solve", {
                "question": question,
                "plan": json.dumps(plan, ensure_ascii=False, indent=2),
                "current_step": json.dumps(step, ensure_ascii=False),
                "step_history": step_history,
                "previous_knowledge": previous_knowledge or "无",
            })

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请完成步骤 {step.get('id', i + 1)}：{step.get('goal', '')}"},
            ]

            step_answer = ""
            result: dict[str, Any] = {}
            for _ in range(3):
                result = await self.call_llm_json(messages, temperature=0.4, model=deep_model)
                if result.get("step_complete"):
                    step_answer = result.get("step_answer", "")
                    break
                messages.append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})
                messages.append({"role": "user", "content": "请继续求解，或给出该步骤的最终答案。"})

            step_result = {
                "step_id": step.get("id", f"S{i + 1}"),
                "goal": step.get("goal", ""),
                "answer": step_answer,
                "self_note": result.get("self_note", ""),
            }
            step_results.append(step_result)

            if step_answer:
                previous_knowledge += f"\n- {step.get('goal', '')}: {step_answer}"
            stream.thinking(f"步骤 {step.get('id', i + 1)}：{step_answer[:100]}...")

        return step_results

    async def _write(
        self,
        question: str,
        plan: dict,
        step_results: list[dict],
        profile_text: str,
        stream: StreamBus,
        deep_model: str,
    ) -> str:
        step_results_text = "\n".join(
            f"### {result['step_id']}: {result['goal']}\n{result['answer']}"
            for result in step_results
        )

        prompt = self.load_prompt("write", {
            "question": question,
            "profile": profile_text or "暂无画像信息",
            "plan": json.dumps(plan, ensure_ascii=False, indent=2),
            "step_results": step_results_text,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请根据以上求解过程，撰写最终的完整答案。"},
        ]

        full_response = ""
        async for chunk in self.stream_llm(messages, temperature=0.7, max_tokens=3000, model=deep_model):
            full_response += chunk
            stream.content(chunk)
        return full_response
