from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any

from config import settings


class DatabaseService:
    """SQLite 持久化服务 — 替代 JSON 文件存储。"""

    def __init__(self, db_path: str = "./data/zhixue.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
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
                    topic TEXT,
                    type TEXT,
                    content TEXT,
                    safety_checked INTEGER DEFAULT 0,
                    safety_issues TEXT,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    id INTEGER PRIMARY KEY AUTOINCREMENT
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
                CREATE INDEX IF NOT EXISTS idx_knowledge_course ON knowledge_docs(course_id);
            """)
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
                """INSERT OR REPLACE INTO resources (id, user_id, topic, type, content, safety_checked, safety_issues, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (resource["id"], resource["user_id"], resource.get("topic"), resource.get("type"),
                 resource.get("content"), 1 if resource.get("safety_checked") else 0,
                 json.dumps(resource.get("safety_issues", []), ensure_ascii=False), resource.get("created_at")),
            )
            conn.commit()
        finally:
            conn.close()

    def get_resources(self, user_id: str, resource_type: str | None = None) -> list[dict]:
        conn = self._get_conn()
        try:
            if resource_type:
                rows = conn.execute(
                    "SELECT * FROM resources WHERE user_id = ? AND type = ? ORDER BY created_at DESC",
                    (user_id, resource_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM resources WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_resource(self, user_id: str, resource_id: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM resources WHERE user_id = ? AND id = ?", (user_id, resource_id)
            ).fetchone()
            return dict(row) if row else None
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

    # ---- Sessions ----

    def add_session_message(self, session_id: str, role: str, content: str) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO sessions (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_session_history(self, session_id: str, limit: int = 40) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT role, content FROM sessions WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        finally:
            conn.close()

    def clear_session(self, session_id: str) -> None:
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
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

    # ---- Stats ----

    def get_stats(self) -> dict:
        conn = self._get_conn()
        try:
            profiles = conn.execute("SELECT COUNT(*) as c FROM profiles").fetchone()["c"]
            resources = conn.execute("SELECT COUNT(*) as c FROM resources").fetchone()["c"]
            sessions = conn.execute("SELECT COUNT(DISTINCT session_id) as c FROM sessions").fetchone()["c"]
            docs = conn.execute("SELECT COUNT(*) as c FROM knowledge_docs").fetchone()["c"]
            return {
                "profiles": profiles,
                "resources": resources,
                "active_sessions": sessions,
                "knowledge_docs": docs,
            }
        finally:
            conn.close()


db = DatabaseService()
