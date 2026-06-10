from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_real_ip(request) -> str:
    """获取真实客户端 IP，支持反向代理 headers。"""
    # 优先从 X-Forwarded-For 获取（反向代理场景）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # X-Real-IP（nginx 常用）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    # 回退到直接连接地址
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip, default_limits=["200/minute"])
