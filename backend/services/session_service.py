from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务。
    
    支持：
    - 多轮对话历史管理
    - LLM 自动摘要压缩
    - 对话结束后自动刷新画像
    """

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}
        self._summaries: dict[str, str] = {}
        self._summary_cache: dict[str, str] = {}
        self._session_times: dict[str, float] = {}
        self._llm_service = None
        self._refresh_lock = asyncio.Lock()
        self._use_db = False
        try:
            from services.database import db
            self._db = db
            self._use_db = True
        except Exception as e:
            logger.warning(f"数据库初始化失败，降级为内存存储: {e}")
            self._db = None

    def _cleanup_expired_sessions(self, max_age_seconds: int = 7200) -> None:
        """清理超过 max_age_seconds 未活动的会话（默认 2 小时）"""
        current_time = time.time()
        expired = [
            sid for sid, last_active in self._session_times.items()
            if current_time - last_active > max_age_seconds
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._session_times.pop(sid, None)
            self._summaries.pop(sid, None)
        if expired:
            logger.info(f"清理了 {len(expired)} 个过期会话")

    @property
    def llm_service(self):
        if self._llm_service is None:
            from services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    def get_history(self, session_id: str, limit: int | None = None, user_id: str = "") -> list[dict]:
        if self._use_db:
            history = self._db.get_session_history(
                session_id,
                limit or settings.MAX_HISTORY_TURNS * 2,
                user_id=user_id,
            )
            return history
        history = self._sessions.get(session_id, [])
        if limit:
            return history[-limit:]
        return history

    def add_message(self, session_id: str, role: str, content: str, user_id: str = "") -> None:
        self._cleanup_expired_sessions()
        self._session_times[session_id] = time.time()
        if self._use_db:
            self._db.add_session_message(user_id or settings.DEFAULT_USER_ID, session_id, role, content)
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

    def clear_session(self, session_id: str, user_id: str = "") -> None:
        self._sessions.pop(session_id, None)
        self._summaries.pop(session_id, None)
        self._session_times.pop(session_id, None)
        if self._use_db:
            self._db.clear_session(session_id, user_id=user_id)

    def list_sessions(self, user_id: str = "") -> list[dict]:
        if self._use_db:
            return self._db.list_sessions(user_id or settings.DEFAULT_USER_ID)
        return [
            {"session_id": sid, "message_count": len(msgs)}
            for sid, msgs in self._sessions.items()
        ]

    async def auto_refresh_memory(self, session_id: str, user_id: str) -> dict:
        """对话后自动刷新画像。
        
        每轮对话结束后异步调用，LLM 判断是否需要更新画像。
        返回 NO_CHANGE 则跳过，否则更新画像。
        """
        async with self._refresh_lock:
            history = self.get_history(session_id, limit=6, user_id=user_id)
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

                from utils import safe_json_parse
                result = safe_json_parse(result_text)
                if result is None:
                    return {"updated": False, "reason": "解析失败"}

                if result.get("should_update") and result.get("updates"):
                    profile_service.update_profile(user_id, result["updates"])
                    return {"updated": True, "updates": result["updates"]}
                
                return {"updated": False, "reason": "无需更新"}

            except Exception as e:
                logger.warning(f"画像自动刷新失败: {e}")
                return {"updated": False, "reason": "更新失败"}

    async def auto_summarize(self, session_id: str) -> str:
        """对话历史过长时自动摘要。"""
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
        except Exception as e:
            logger.warning(f"自动摘要失败: {e}")
            return existing_summary

    async def generate_session_summary(self, session_id: str, user_id: str) -> str:
        cache_key = f"{user_id}:{session_id}"
        if cache_key in self._summary_cache:
            logger.debug("使用缓存的会话摘要: %s", cache_key)
            return self._summary_cache[cache_key]

        history = self.get_history(session_id, user_id=user_id)
        if len(history) < 2:
            return ""

        conversation = "\n".join(
            f"{m['role']}: {m['content'][:300]}" for m in history
        )

        prompt = f"""请为以下对话生成一个结构化摘要。

对话内容：
{conversation}

请按以下格式生成摘要（不超过500字）：
【讨论主题】简要说明本次对话的主要话题
【关键问题】列出学生提出的核心问题（1-3个）
【学习成果】总结学生通过对话获得的知识或理解

使用中文，保持简洁。"""

        try:
            messages = [{"role": "user", "content": prompt}]
            summary = await self.llm_service.chat(messages=messages, temperature=0.3, max_tokens=600)
            self._summary_cache[cache_key] = summary
            logger.info("生成会话摘要: session=%s, user=%s", session_id, user_id)
            return summary
        except Exception as e:
            logger.error("生成会话摘要失败: %s", str(e))
            return ""

    def compress_history(self, history: list[dict], max_tokens: int = 2000) -> list[dict]:
        if not history:
            return []

        compressed = []
        token_count = 0

        important_keywords = ["问题", "答案", "概念", "原理", "定义", "公式", "定理", "方法", "步骤", "注意", "重点", "关键", "核心", "总结"]

        for msg in history:
            content = msg.get("content", "")
            role = msg.get("role", "")

            if role == "system":
                compressed.append(msg)
                continue

            estimated_tokens = len(content) // 2

            if role == "user":
                if any(keyword in content for keyword in important_keywords):
                    compressed.append(msg)
                    token_count += estimated_tokens
                elif len(content) > 20:
                    trimmed = content[:200] + "..." if len(content) > 200 else content
                    compressed.append({"role": role, "content": trimmed})
                    token_count += len(trimmed) // 2
            elif role == "assistant":
                if any(keyword in content for keyword in important_keywords):
                    compressed.append(msg)
                    token_count += estimated_tokens
                elif len(content) > 50:
                    trimmed = content[:300] + "..." if len(content) > 300 else content
                    compressed.append({"role": role, "content": trimmed})
                    token_count += len(trimmed) // 2

            if token_count >= max_tokens:
                break

        if token_count >= max_tokens and len(compressed) > 2:
            system_msgs = [m for m in compressed if m.get("role") == "system"]
            non_system = [m for m in compressed if m.get("role") != "system"]
            keep_count = max(4, len(non_system) // 2)
            compressed = system_msgs + non_system[-keep_count:]

        logger.debug("压缩对话历史: %d 条 -> %d 条", len(history), len(compressed))
        return compressed

    def get_learning_progress(self, user_id: str) -> dict:
        if self._use_db:
            try:
                sessions = self._db.list_sessions(user_id)
                total_messages = 0
                topics = set()

                for session in sessions:
                    session_id = session.get("session_id", "")
                    history = self._db.get_session_history(session_id, limit=100, user_id=user_id)
                    total_messages += len(history)

                    for msg in history:
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            if "问题" in content or "什么是" in content or "如何" in content or "怎么" in content:
                                words = content[:50].split()
                                if words:
                                    topics.add(words[0])

                topic_list = list(topics)[:20]
                mastery_score = min(100, total_messages * 2)

                return {
                    "session_count": len(sessions),
                    "total_messages": total_messages,
                    "topics_covered": topic_list,
                    "average_mastery": mastery_score,
                }
            except Exception as e:
                logger.error("获取学习进度失败: %s", str(e))

        session_count = len(self._sessions)
        total_messages = sum(len(msgs) for msgs in self._sessions.values())

        return {
            "session_count": session_count,
            "total_messages": total_messages,
            "topics_covered": [],
            "average_mastery": min(100, total_messages * 2),
        }

    def get_recent_topics(self, user_id: str, limit: int = 5) -> list[dict]:
        topics = []

        if self._use_db:
            try:
                sessions = self._db.list_sessions(user_id)
                for session in sessions[-limit:]:
                    session_id = session.get("session_id", "")
                    history = self._db.get_session_history(session_id, limit=4, user_id=user_id)

                    for msg in history:
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            if len(content) > 10:
                                topics.append({
                                    "session_id": session_id,
                                    "topic": content[:100],
                                    "timestamp": msg.get("timestamp", ""),
                                })
                                break
            except Exception as e:
                logger.error("获取最近话题失败: %s", str(e))

        topics = topics[-limit:]
        topics.reverse()

        logger.debug("获取最近话题: user=%s, count=%d", user_id, len(topics))
        return topics


session_service = SessionService()
