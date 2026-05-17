from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from typing import Any

from config import settings

logger = logging.getLogger("zhixue.database")


class DatabaseService:
    """SQLite 持久化服务 — 替代 JSON 文件存储。"""

    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "zhixue.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        logger.info(f"数据库初始化完成: {db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS mastery (
                    user_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    level REAL DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    correct INTEGER DEFAULT 0,
                    last_practice REAL,
                    history TEXT DEFAULT '[]',
                    PRIMARY KEY (user_id, topic_id)
                );

                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    course_id TEXT,
                    topic TEXT,
                    type TEXT,
                    content TEXT,
                    file_name TEXT,
                    source TEXT,
                    safety_checked INTEGER DEFAULT 0,
                    safety_issues TEXT,
                    safety_suggestions TEXT DEFAULT '[]',
                    is_safe INTEGER DEFAULT 1,
                    sources_used TEXT DEFAULT '[]',
                    resource_meta TEXT DEFAULT '{}',
                    created_at REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT NOT NULL DEFAULT '',
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                );

                CREATE TABLE IF NOT EXISTS resource_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    course_id TEXT,
                    resource_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source_page TEXT,
                    payload TEXT DEFAULT '{}',
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS knowledge_docs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT NOT NULL,
                    filename TEXT,
                    content TEXT,
                    chunk_index INTEGER,
                    embedding_id TEXT,
                    created_at REAL
                );

                CREATE INDEX IF NOT EXISTS idx_mastery_user ON mastery(user_id);
                CREATE INDEX IF NOT EXISTS idx_resources_user ON resources(user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_id ON sessions(session_id);
                CREATE TABLE IF NOT EXISTS knowledge_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kb_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    document_count INTEGER DEFAULT 0,
                    note TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    is_current INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_course ON knowledge_docs(course_id);
                CREATE INDEX IF NOT EXISTS idx_kb_versions_name ON knowledge_versions(kb_name);

                CREATE TABLE IF NOT EXISTS sr_cards (
                    user_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    interval_val INTEGER DEFAULT 0,
                    easiness REAL DEFAULT 2.5,
                    repetitions INTEGER DEFAULT 0,
                    next_review REAL DEFAULT 0,
                    last_review REAL,
                    review_history TEXT DEFAULT '[]',
                    PRIMARY KEY (user_id, topic_id)
                );

                CREATE INDEX IF NOT EXISTS idx_sr_cards_user ON sr_cards(user_id);
            """)

            # Migrate: add file_name column if missing
            cols = [r[1] for r in conn.execute("PRAGMA table_info(resources)").fetchall()]
            if "file_name" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN file_name TEXT")
            if "course_id" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN course_id TEXT")
            if "source" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN source TEXT")
            if "safety_suggestions" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN safety_suggestions TEXT DEFAULT '[]'")
            if "is_safe" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN is_safe INTEGER DEFAULT 1")
            if "sources_used" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN sources_used TEXT DEFAULT '[]'")
            if "resource_meta" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN resource_meta TEXT DEFAULT '{}'")
            if "updated_at" not in cols:
                conn.execute("ALTER TABLE resources ADD COLUMN updated_at REAL")

            session_cols = [r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()]
            if "user_id" not in session_cols:
                conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")

            conn.commit()
        finally:
            conn.close()

    # ---- Profile ----

    def get_profile(self, user_id: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT data FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
            return json.loads(row["data"]) if row else None
        finally:
            conn.close()

    def save_profile(self, user_id: str, data: dict) -> None:
        conn = self._get_conn()
        try:
            now = time.time()
            conn.execute(
                "INSERT OR REPLACE INTO profiles (user_id, data, created_at, updated_at) VALUES (?, ?, COALESCE((SELECT created_at FROM profiles WHERE user_id = ?), ?), ?)",
                (user_id, json.dumps(data, ensure_ascii=False), user_id, now, now),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- Mastery ----

    def get_user_mastery(self, user_id: str) -> dict[str, dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM mastery WHERE user_id = ?", (user_id,)).fetchall()
            result = {}
            for row in rows:
                result[row["topic_id"]] = {
                    "level": row["level"],
                    "attempts": row["attempts"],
                    "correct": row["correct"],
                    "last_practice": row["last_practice"],
                    "history": json.loads(row["history"] or "[]"),
                }
            return result
        finally:
            conn.close()

    def save_mastery(self, user_id: str, topic_id: str, data: dict) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO mastery (user_id, topic_id, level, attempts, correct, last_practice, history)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, topic_id, data["level"], data["attempts"], data["correct"],
                 data.get("last_practice"), json.dumps(data.get("history", []), ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- Resources ----

    def save_resource(self, resource: dict) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO resources (
                       id, user_id, course_id, topic, type, content, file_name, source,
                       safety_checked, safety_issues, safety_suggestions, is_safe,
                       sources_used, resource_meta, created_at, updated_at
                   )
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (resource["id"], resource["user_id"], resource.get("course_id"), resource.get("topic"), resource.get("type"),
                 resource.get("content"), resource.get("file_name"),
                 resource.get("source"),
                 1 if resource.get("safety_checked") else 0,
                 json.dumps(resource.get("safety_issues", []), ensure_ascii=False),
                 json.dumps(resource.get("safety_suggestions", []), ensure_ascii=False),
                 1 if resource.get("is_safe", True) else 0,
                 json.dumps(resource.get("sources_used", []), ensure_ascii=False),
                 json.dumps(resource.get("resource_meta", {}), ensure_ascii=False),
                 resource.get("created_at"), resource.get("updated_at")),
            )
            conn.commit()
        finally:
            conn.close()

    def get_resources(self, user_id: str, resource_type: str | None = None, course_id: str | None = None) -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM resources WHERE user_id = ?"
            params: list[Any] = [user_id]
            if resource_type:
                query += " AND type = ?"
                params.append(resource_type)
            if course_id:
                query += " AND course_id = ?"
                params.append(course_id)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._deserialize_resource(dict(row)) for row in rows]
        finally:
            conn.close()

    def get_resource(self, user_id: str, resource_id: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM resources WHERE user_id = ? AND id = ?", (user_id, resource_id)
            ).fetchone()
            return self._deserialize_resource(dict(row)) if row else None
        finally:
            conn.close()

    def delete_resource(self, user_id: str, resource_id: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM resources WHERE user_id = ? AND id = ?", (user_id, resource_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_resource_content(self, resource_id: str, user_id: str, content: str) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE resources SET content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (content, time.time(), resource_id, user_id),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- Sessions ----

    def add_session_message(self, user_id: str, session_id: str, role: str, content: str) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO sessions (user_id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, session_id, role, content, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_session_history(self, session_id: str, limit: int = 40, user_id: str = "") -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT role, content FROM sessions WHERE session_id = ?"
            params: list[Any] = [session_id]
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, tuple(params)).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        finally:
            conn.close()

    def clear_session(self, session_id: str, user_id: str = "") -> None:
        conn = self._get_conn()
        try:
            if user_id:
                conn.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            else:
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()

    def list_sessions(self, user_id: str) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT session_id, COUNT(*) as cnt, MAX(id) as last_id
                FROM sessions
                WHERE user_id = ?
                GROUP BY session_id
                ORDER BY last_id DESC
                """,
                (user_id,),
            ).fetchall()
            return [{"session_id": row["session_id"], "message_count": row["cnt"]} for row in rows]
        finally:
            conn.close()

    def record_resource_event(
        self,
        user_id: str,
        resource_id: str,
        event_type: str,
        course_id: str = "",
        source_page: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO resource_events (user_id, course_id, resource_id, event_type, source_page, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    course_id,
                    resource_id,
                    event_type,
                    source_page,
                    json.dumps(payload or {}, ensure_ascii=False),
                    time.time(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_resource_events(self, user_id: str, resource_id: str | None = None) -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM resource_events WHERE user_id = ?"
            params: list[Any] = [user_id]
            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, tuple(params)).fetchall()
            events = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item.get("payload") or "{}")
                events.append(item)
            return events
        finally:
            conn.close()

    # ---- Knowledge Docs ----

    def save_knowledge_chunk(self, course_id: str, filename: str, content: str, chunk_index: int) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO knowledge_docs (course_id, filename, content, chunk_index, created_at) VALUES (?, ?, ?, ?, ?)",
                (course_id, filename, content, chunk_index, time.time()),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_knowledge_chunks(self, course_id: str) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM knowledge_docs WHERE course_id = ? ORDER BY chunk_index",
                (course_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ---- Knowledge Versions ----

    def create_kb_version(self, kb_name: str, document_count: int, note: str = "") -> int:
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE knowledge_versions SET is_current = 0 WHERE kb_name = ? AND is_current = 1",
                (kb_name,),
            )
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 AS next_ver FROM knowledge_versions WHERE kb_name = ?",
                (kb_name,),
            ).fetchone()
            next_version = row["next_ver"]
            cursor = conn.execute(
                "INSERT INTO knowledge_versions (kb_name, version, document_count, note, created_at, is_current) VALUES (?, ?, ?, ?, ?, 1)",
                (kb_name, next_version, document_count, note, time.time()),
            )
            conn.commit()
            logger.info(f"知识库 {kb_name} 创建版本 v{next_version}, 文档数: {document_count}")
            return next_version
        finally:
            conn.close()

    def get_kb_versions(self, kb_name: str) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM knowledge_versions WHERE kb_name = ? ORDER BY version DESC",
                (kb_name,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_current_version(self, kb_name: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM knowledge_versions WHERE kb_name = ? AND is_current = 1",
                (kb_name,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def set_current_version(self, kb_name: str, version: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE knowledge_versions SET is_current = 0 WHERE kb_name = ? AND is_current = 1",
                (kb_name,),
            )
            cursor = conn.execute(
                "UPDATE knowledge_versions SET is_current = 1 WHERE kb_name = ? AND version = ?",
                (kb_name, version),
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"知识库 {kb_name} 切换到版本 v{version}")
            return success
        finally:
            conn.close()

    # ---- Stats ----

    def get_stats(self) -> dict:
        conn = self._get_conn()
        try:
            profiles = conn.execute("SELECT COUNT(*) as c FROM profiles").fetchone()["c"]
            resources = conn.execute("SELECT COUNT(*) as c FROM resources").fetchone()["c"]
            sessions = conn.execute("SELECT COUNT(DISTINCT session_id) as c FROM sessions").fetchone()["c"]
            resource_events = conn.execute("SELECT COUNT(*) as c FROM resource_events").fetchone()["c"]
            docs = conn.execute("SELECT COUNT(*) as c FROM knowledge_docs").fetchone()["c"]
            return {
                "profiles": profiles,
                "resources": resources,
                "active_sessions": sessions,
                "resource_events": resource_events,
                "knowledge_docs": docs,
            }
        finally:
            conn.close()

    @staticmethod
    def _deserialize_resource(resource: dict[str, Any]) -> dict[str, Any]:
        resource["safety_issues"] = json.loads(resource.get("safety_issues") or "[]")
        resource["safety_suggestions"] = json.loads(resource.get("safety_suggestions") or "[]")
        resource["sources_used"] = json.loads(resource.get("sources_used") or "[]")
        resource["resource_meta"] = json.loads(resource.get("resource_meta") or "{}")
        resource["safety_status"] = {
            "checked": bool(resource.get("safety_checked")),
            "is_safe": bool(resource.get("is_safe", 1)),
            "issues": resource["safety_issues"],
            "suggestions": resource["safety_suggestions"],
        }
        return resource


db = DatabaseService()
