from __future__ import annotations

import json
from typing import Any

from core.agent import BaseAgent
from core.context import UnifiedContext
from core.stream_bus import StreamBus
from config import settings


class DeepSolveAgent(BaseAgent):
    """Deep Solve Agent — Plan → Solve → Write 三阶段管线。
    
    参考 DeepTutor 的 Deep Solve 设计：
    1. PlannerAgent: 分析问题，制定求解计划
    2. SolverAgent: ReAct 循环，逐步求解
    3. WriterAgent: 撰写最终解答
    
    使用 DeepSeek V3.2 模型进行深度推理。
    """

    DEEP_MODEL = "deepseek-ai/DeepSeek-V3.2"

    def __init__(self) -> None:
        super().__init__(agent_name="deep_solve_agent", module_name="solve")

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("deep_solve", "正在分析问题...")

        from services.profile_service import profile_service
        from services.mastery_service import mastery_service

        profile = profile_service.get_profile(ctx.user_id)
        mastery = mastery_service.get_user_mastery(ctx.user_id)
        profile_text = profile_service.get_profile_context_text(ctx.user_id)

        # ===== 阶段1: 规划 =====
        stream.stage_start("plan", "正在制定求解计划...")
        plan = await self._plan(ctx.user_message, profile_text, mastery, stream)
        stream.stage_end("plan")

        # ===== 阶段2: 逐步求解 =====
        stream.stage_start("solve", "正在逐步求解...")
        step_results = await self._solve(ctx.user_message, plan, profile_text, mastery, stream)
        stream.stage_end("solve")

        # ===== 阶段3: 撰写解答 =====
        stream.stage_start("write", "正在撰写解答...")
        final_answer = await self._write(ctx.user_message, plan, step_results, profile_text, stream)
        stream.stage_end("write")

        stream.stage_end("deep_solve")

        return {
            "plan": plan,
            "step_results": step_results,
            "response": final_answer,
        }

    async def _plan(self, question: str, profile_text: str, mastery: dict, stream: StreamBus) -> dict:
        prompt = self.load_prompt("plan", {
            "profile": profile_text or "暂无画像信息",
            "mastery": json.dumps(mastery, ensure_ascii=False, indent=2),
            "question": question,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请为以下问题制定求解计划：{question}"},
        ]

        result = await self.call_llm_json(messages, temperature=0.3, model=self.DEEP_MODEL)
        stream.thinking(f"求解计划：{len(result.get('steps', []))} 个步骤")
        return result

    async def _solve(
        self, question: str, plan: dict, profile_text: str, mastery: dict, stream: StreamBus
    ) -> list[dict]:
        steps = plan.get("steps", [])
        step_results = []
        previous_knowledge = ""

        for i, step in enumerate(steps):
            stream.progress(i + 1, len(steps), f"正在求解步骤 {step.get('id', i+1)}")

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
                {"role": "user", "content": f"请求解步骤 {step.get('id', i+1)}: {step.get('goal', '')}"},
            ]

            max_retries = 3
            step_complete = False
            step_answer = ""

            for attempt in range(max_retries):
                result = await self.call_llm_json(messages, temperature=0.4, model=self.DEEP_MODEL)

                if result.get("step_complete"):
                    step_complete = True
                    step_answer = result.get("step_answer", "")
                    break

                messages.append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})
                messages.append({"role": "user", "content": "请继续求解，或给出该步骤的最终答案。"})

            step_result = {
                "step_id": step.get("id", f"S{i+1}"),
                "goal": step.get("goal", ""),
                "answer": step_answer,
                "self_note": result.get("self_note", ""),
            }
            step_results.append(step_result)

            if step_answer:
                previous_knowledge += f"\n- {step.get('goal', '')}: {step_answer}"

            stream.thinking(f"步骤 {step.get('id', i+1)}: {step_answer[:100]}...")

        return step_results

    async def _write(
        self, question: str, plan: dict, step_results: list, profile_text: str, stream: StreamBus
    ) -> str:
        step_results_text = "\n".join(
            f"### {r['step_id']}: {r['goal']}\n{r['answer']}"
            for r in step_results
        )

        prompt = self.load_prompt("write", {
            "question": question,
            "profile": profile_text or "暂无画像信息",
            "plan": json.dumps(plan, ensure_ascii=False, indent=2),
            "step_results": step_results_text,
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请根据以上求解过程，撰写最终的完整解答。"},
        ]

        full_response = ""
        async for chunk in self.stream_llm(messages, temperature=0.7, max_tokens=3000, model=self.DEEP_MODEL):
            full_response += chunk
            stream.content(chunk)

        return full_response
