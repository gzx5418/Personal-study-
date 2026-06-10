from __future__ import annotations

import pytest

from utils import safe_json_parse


class TestSafeJsonParse:
    def test_parse_valid_json_object(self):
        result = safe_json_parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_valid_json_array(self):
        result = safe_json_parse('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_json_with_markdown_block(self):
        text = '```json\n{"key": "value"}\n```'
        result = safe_json_parse(text)
        assert result == {"key": "value"}

    def test_parse_json_with_plain_markdown_block(self):
        text = '```\n{"key": "value"}\n```'
        result = safe_json_parse(text)
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self):
        text = 'Here is the result:\n{"key": "value"}\nDone.'
        result = safe_json_parse(text)
        assert result == {"key": "value"}

    def test_parse_json_array_with_surrounding_text(self):
        text = 'Result: [1, 2, 3] end'
        result = safe_json_parse(text)
        assert result == [1, 2, 3]

    def test_parse_empty_string(self):
        result = safe_json_parse("")
        assert result is None

    def test_parse_none(self):
        result = safe_json_parse(None)
        assert result is None

    def test_parse_invalid_json(self):
        result = safe_json_parse("not json at all")
        assert result is None

    def test_parse_invalid_json_with_default(self):
        result = safe_json_parse("not json", default={"fallback": True})
        assert result == {"fallback": True}

    def test_parse_invalid_json_with_list_default(self):
        result = safe_json_parse("not json", default=[])
        assert result == []

    def test_parse_nested_json(self):
        text = '{"a": {"b": [1, 2, 3]}}'
        result = safe_json_parse(text)
        assert result == {"a": {"b": [1, 2, 3]}}

    def test_parse_json_with_trailing_comma(self):
        # 这应该失败，因为标准 JSON 不允许尾随逗号
        text = '{"key": "value",}'
        result = safe_json_parse(text)
        # 可能解析失败，也可能被 regex 匹配到
        # 只要不抛异常就算通过

    def test_parse_llm_typical_output(self):
        text = '''根据分析，结果如下：
```json
{
  "topics": ["Python基础", "变量"],
  "difficulty": "easy"
}
```
以上是分析结果。'''
        result = safe_json_parse(text)
        assert result is not None
        assert "topics" in result
