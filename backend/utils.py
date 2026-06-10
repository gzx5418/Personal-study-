from __future__ import annotations

import json
import re


def safe_json_parse(text: str, default=None):
    """从 LLM 输出中安全解析 JSON。

    处理常见的 LLM 输出格式：
    - 纯 JSON
    - 带 markdown 代码块的 JSON (```json ... ```)
    - JSON 被其他文本包裹的情况

    Args:
        text: LLM 输出文本
        default: 解析失败时的默认值

    Returns:
        解析后的 dict/list，或 default
    """
    if not text:
        return default

    # 限制输入长度，防止 ReDoS
    if len(text) > 50_000:
        text = text[:50_000]

    text = text.strip()

    # 移除 markdown 代码块
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取第一个 JSON 对象或数组（使用 find/rfind，无正则）
    for open_char, close_char in [("{", "}"), ("[", "]")]:
        start = text.find(open_char)
        end = text.rfind(close_char)
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    # 正则兜底（使用非贪婪匹配，限制长度）
    match = re.search(r'(\{[^{}]*\}|\[[^\[\]]*\])', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return default
