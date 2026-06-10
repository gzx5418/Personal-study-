from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path

import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings

logger = logging.getLogger("zhixue.auth")

# JWT 配置 — 强制要求环境变量设置
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # 自动生成随机密钥（每次重启后旧 token 失效，仅适用于开发环境）
    JWT_SECRET = secrets.token_hex(32)
    logger.warning("JWT_SECRET 未设置，已自动生成随机密钥（重启后旧 token 失效）。生产环境请设置 JWT_SECRET 环境变量。")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 用户数据文件
USERS_FILE = Path(os.path.dirname(settings.PROFILE_FILE)) / "users.json"

security = HTTPBearer(auto_error=False)


def _hash_password(password: str, salt: str | None = None) -> str:
    """密码哈希（PBKDF2-SHA256，每次生成随机 salt）。"""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=100_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """验证密码。stored_hash 格式: salt$hash"""
    if "$" not in stored_hash:
        # 兼容旧格式（SHA-256 静态 salt）
        old_hash = hashlib.sha256(f"zhixue_salt_2024{password}".encode()).hexdigest()
        return hmac.compare_digest(old_hash, stored_hash)
    salt, _ = stored_hash.split("$", 1)
    return hmac.compare_digest(_hash_password(password, salt), stored_hash)


def _load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_users(users: dict) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 原子写入：先写临时文件再重命名
    tmp_path = USERS_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    tmp_path.replace(USERS_FILE)


def create_token(user_id: str) -> str:
    """生成 JWT token。"""
    payload = {
        "sub": user_id,
        "iat": time.time(),
        "exp": time.time() + JWT_EXPIRE_HOURS * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> str | None:
    """验证 JWT token，返回 user_id 或 None。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def register_user(user_id: str, password: str, name: str = "") -> dict:
    """注册新用户。"""
    users = _load_users()
    if user_id in users:
        raise HTTPException(status_code=409, detail="用户已存在")
    users[user_id] = {
        "password_hash": _hash_password(password),
        "name": name or user_id,
        "created_at": time.time(),
    }
    _save_users(users)
    token = create_token(user_id)
    return {"user_id": user_id, "token": token, "name": name or user_id}


def authenticate_user(user_id: str, password: str) -> dict:
    """验证用户凭据。"""
    users = _load_users()
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_token(user_id)
    return {"user_id": user_id, "token": token, "name": user.get("name", user_id)}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI 依赖：从 Bearer token 中提取 user_id。

    如果没有 token，返回默认用户（开发模式）。
    """
    if credentials is None:
        if os.getenv("AUTH_REQUIRED", "false").lower() != "true":
            return settings.DEFAULT_USER_ID
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return user_id


async def get_current_user_strict(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI 依赖：严格模式，必须提供有效 token。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return user_id
