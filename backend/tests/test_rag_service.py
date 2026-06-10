from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def rag_service(tmp_path):
    """创建隔离的 RAG 服务实例。"""
    kb_dir = tmp_path / "knowledge_bases"
    kb_dir.mkdir()

    # 创建测试知识库
    kb_data = {
        "py_intro": {
            "title": "Python3 简介",
            "chapter": "第0章 准备",
            "content": "Python 是一种解释型、面向对象的高级编程语言。Guido van Rossum 创建了 Python。",
        },
        "py_variable": {
            "title": "变量与赋值",
            "chapter": "第1章 基础语法",
            "content": "变量是用来存储数据的容器。Python 中不需要声明变量类型。赋值使用 = 运算符。",
        },
        "py_list": {
            "title": "列表",
            "chapter": "第2章 数据类型",
            "content": "列表是 Python 中最常用的数据结构。使用方括号 [] 创建。列表是可变的有序序列。",
        },
        "py_dict": {
            "title": "字典",
            "chapter": "第2章 数据类型",
            "content": "字典是键值对的集合。使用花括号 {} 创建。字典的键必须是不可变类型。",
        },
    }
    with open(kb_dir / "test_course.json", "w", encoding="utf-8") as f:
        json.dump(kb_data, f, ensure_ascii=False)

    with patch("config.settings.KNOWLEDGE_DIR", str(kb_dir)):
        import importlib
        import services.rag_service as rag_mod
        importlib.reload(rag_mod)
        svc = rag_mod.RAGService()
        yield svc


class TestTokenize:
    def test_english_tokens(self, rag_service):
        tokens = rag_service._tokenize("hello world python")
        assert "hello" in tokens
        assert "world" in tokens
        assert "python" in tokens

    def test_chinese_tokens(self, rag_service):
        tokens = rag_service._tokenize("变量赋值")
        assert "变量" in tokens
        assert "赋值" in tokens
        # bigrams
        assert "量赋" in tokens

    def test_mixed_tokens(self, rag_service):
        tokens = rag_service._tokenize("Python变量")
        assert "python" in tokens
        assert "变量" in tokens

    def test_empty_string(self, rag_service):
        tokens = rag_service._tokenize("")
        assert tokens == []

    def test_numbers(self, rag_service):
        tokens = rag_service._tokenize("python3 version 3.11")
        assert "python3" in tokens
        assert "version" in tokens
        assert "3" in tokens


class TestSimpleSearch:
    def test_search_exact_match(self, rag_service):
        results = rag_service._simple_search("列表", top_k=3, kb_name="test_course")
        assert len(results) > 0
        assert any("列表" in r["title"] for r in results)

    def test_search_partial_match(self, rag_service):
        results = rag_service._simple_search("Python简介", top_k=3, kb_name="test_course")
        assert len(results) > 0

    def test_search_no_match(self, rag_service):
        results = rag_service._simple_search("量子力学", top_k=3, kb_name="test_course")
        assert len(results) == 0

    def test_search_returns_sorted(self, rag_service):
        results = rag_service._simple_search("数据", top_k=5, kb_name="test_course")
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["score"] >= results[i + 1]["score"]

    def test_search_respects_top_k(self, rag_service):
        results = rag_service._simple_search("Python", top_k=1, kb_name="test_course")
        assert len(results) <= 1


class TestBM25Search:
    def test_bm25_basic(self, rag_service):
        results = rag_service._bm25_search("变量", kb_name="test_course", top_k=3)
        assert len(results) > 0
        assert any("变量" in r["title"] for r in results)

    def test_bm25_empty_query(self, rag_service):
        results = rag_service._bm25_search("", kb_name="test_course", top_k=3)
        assert results == []


class TestGetContextForTopic:
    def test_returns_context(self, rag_service):
        result = rag_service.get_context_for_topic("列表", kb_name="test_course")
        assert "context" in result
        assert "sources" in result
        assert len(result["context"]) > 0
        assert len(result["sources"]) > 0

    def test_returns_empty_for_no_match(self, rag_service):
        result = rag_service.get_context_for_topic("量子力学", kb_name="test_course")
        assert result["context"] == ""
        assert result["sources"] == []


class TestKnowledgeBases:
    def test_list_knowledge_bases(self, rag_service):
        bases = rag_service.list_knowledge_bases()
        assert "test_course" in bases

    def test_kb_has_correct_data(self, rag_service):
        kb = rag_service._simple_kbs.get("test_course", {})
        assert len(kb) == 4
        assert "py_intro" in kb
        assert kb["py_intro"]["title"] == "Python3 简介"
