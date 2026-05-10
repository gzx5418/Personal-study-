from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from config import settings


class SessionService:
    """会话管理服务，参考 DeepTutor 设计。
    
    支持：
    - 多轮对话历史管理
    - LLM 自动摘要压缩（参考 DeepTutor ContextBuilder）
    - 对话结束后自动刷新画像（参考 DeepTutor MemoryService）
    """

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}
        self._summaries: dict[str, str] = {}
        self._llm_service = None
        self._refresh_lock = asyncio.Lock()
        self._use_db = False
        try:
            from services.database import db
            self._db = db
            self._use_db = True
        except Exception:
            self._db = None

    @property
    def llm_service(self):
        if self._llm_service is None:
            from services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    def get_history(self, session_id: str, limit: int | None = None) -> list[dict]:
        if self._use_db:
            history = self._db.get_session_history(session_id, limit or settings.MAX_HISTORY_TURNS * 2)
            return history
        history = self._sessions.get(session_id, [])
        if limit:
            return history[-limit:]
        return history

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if self._use_db:
            self._db.add_session_message(session_id, role, content)
            return
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": role,
            "content": content,
        })
        if len(self._sessions[session_id]) > settings.MAX_HISTORY_TURNS * 2:
            self._sessions[session_id] = self._sessions[session_id][-settings.MAX_HISTORY_TURNS * 2:]

    def get_summary(self, session_id: str) -> str:
        return self._summaries.get(session_id, "")

    def set_summary(self, session_id: str, summary: str) -> None:
        self._summaries[session_id] = summary

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._summaries.pop(session_id, None)
        if self._use_db:
            self._db.clear_session(session_id)

    def list_sessions(self) -> list[dict]:
        if self._use_db:
            conn = self._db._get_conn()
            try:
                rows = conn.execute(
                    "SELECT session_id, COUNT(*) as cnt FROM sessions GROUP BY session_id ORDER BY MAX(id) DESC"
                ).fetchall()
                return [{"session_id": row["session_id"], "message_count": row["cnt"]} for row in rows]
            finally:
                conn.close()
        return [
            {"session_id": sid, "message_count": len(msgs)}
            for sid, msgs in self._sessions.items()
        ]

    async def auto_refresh_memory(self, session_id: str, user_id: str) -> dict:
        """对话后自动刷新画像 — 参考 DeepTutor MemoryService.refresh_from_turn()。
        
        每轮对话结束后异步调用，LLM 判断是否需要更新画像。
        返回 NO_CHANGE 则跳过，否则更新画像。
        """
        async with self._refresh_lock:
            history = self.get_history(session_id, limit=6)
            if len(history) < 2:
                return {"updated": False, "reason": "对话太短"}

            from services.profile_service import profile_service
            current_profile = profile_service.get_profile(user_id)

            conversation = "\n".join(
                f"{m['role']}: {m['content'][:200]}" for m in history[-6:]
            )

            prompt = f"""你是学生画像自动分析系统。请根据最近对话，判断是否需要更新学生画像。

当前画像：
{json.dumps(current_profile, ensure_ascii=False, indent=2)}

最近对话：
{conversation}

规则：
- 只在有明确证据时更新
- 如果不需要更新，返回 {{"should_update": false}}
- 如果需要更新，返回 {{"should_update": true, "updates": {{...}}}} 
- updates 只包含变化的字段
- 不确定的信息不要更新

输出 JSON："""

            try:
                messages = [{"role": "user", "content": prompt}]
                result_text = await self.llm_service.chat(
                    messages=messages, temperature=0.2, max_tokens=500
                )

                try:
                    result = json.loads(result_text)
                except json.JSONDecodeError:
                    start = result_text.find("{")
                    end = result_text.rfind("}") + 1
                    if start >= 0 and end > start:
                        result = json.loads(result_text[start:end])
                    else:
                        return {"updated": False, "reason": "解析失败"}

                if result.get("should_update") and result.get("updates"):
                    profile_service.update_profile(user_id, result["updates"])
                    return {"updated": True, "updates": result["updates"]}
                
                return {"updated": False, "reason": "无需更新"}

            except Exception as e:
                return {"updated": False, "reason": str(e)}

    async def auto_summarize(self, session_id: str) -> str:
        """对话历史过长时自动摘要 — 参考 DeepTutor ContextBuilder 设计。"""
        history = self.get_history(session_id)
        if len(history) < 10:
            return self.get_summary(session_id)

        existing_summary = self.get_summary(session_id)
        recent_messages = history[-8:]
        old_messages = history[:-8]

        old_text = "\n".join(f"{m['role']}: {m['content'][:150]}" for m in old_messages)

        prompt = f"""请将以下对话历史压缩为简洁的摘要，保留关键信息和学习要点。

已有摘要：
{existing_summary or "无"}

对话历史：
{old_text}

要求：
- 保留学生提到的关键问题和困惑
- 保留重要的知识点和结论
- 不超过 200 字
- 使用中文"""

        try:
            messages = [{"role": "user", "content": prompt}]
            summary = await self.llm_service.chat(messages=messages, temperature=0.3, max_tokens=300)
            self.set_summary(session_id, summary)
            return summary
        except Exception:
            return existing_summary


session_service = SessionService()
