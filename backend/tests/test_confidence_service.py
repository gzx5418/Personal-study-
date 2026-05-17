from __future__ import annotations

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.confidence_service import ConfidenceService


@pytest.fixture
def service():
    return ConfidenceService()


@pytest.fixture
def sample_results():
    return [
        {"title": "Python装饰器", "content": "装饰器是Python中的高级函数", "snippet": "装饰器用于修改函数行为", "score": 0.9},
        {"title": "装饰器详解", "content": "装饰器是一种设计模式", "snippet": "Python装饰器使用@语法", "score": 0.7},
        {"title": "装饰器教程", "content": "学习Python装饰器", "snippet": "装饰器可以简化代码", "score": 0.5},
    ]


@pytest.fixture
def uniform_results():
    return [
        {"title": "结果1", "content": "内容1", "snippet": "片段1", "score": 1.0},
        {"title": "结果2", "content": "内容2", "snippet": "片段2", "score": 1.0},
        {"title": "结果3", "content": "内容3", "snippet": "片段3", "score": 1.0},
    ]


@pytest.fixture
def skewed_results():
    return [
        {"title": "高分结果", "content": "内容", "snippet": "片段", "score": 10.0},
        {"title": "低分结果", "content": "内容", "snippet": "片段", "score": 0.01},
        {"title": "极低分结果", "content": "内容", "snippet": "片段", "score": 0.001},
    ]


class TestConfidenceCalculation:
    def test_no_results(self, service):
        result = service.calculate_confidence("test query", [])
        assert result["score"] == 0
        assert result["breakdown"]["consistency"] == 0
        assert result["breakdown"]["relevance"] == 0
        assert result["breakdown"]["match"] == 0

    def test_with_results_no_content(self, service, sample_results):
        result = service.calculate_confidence("Python装饰器", sample_results)
        assert 0 <= result["score"] <= 100
        assert "consistency" in result["breakdown"]
        assert "relevance" in result["breakdown"]
        assert "match" in result["breakdown"]
        assert result["breakdown"]["match"] == 0

    def test_with_results_and_content(self, service, sample_results):
        content = "装饰器是Python中的高级函数"
        result = service.calculate_confidence("Python装饰器", sample_results, content=content)
        assert 0 <= result["score"] <= 100
        assert result["breakdown"]["match"] >= 0

    def test_score_range(self, service, sample_results):
        result = service.calculate_confidence("Python", sample_results, content="Python编程")
        assert 0 <= result["score"] <= 100

    def test_breakdown_values_range(self, service, sample_results):
        result = service.calculate_confidence("Python", sample_results, content="Python编程")
        for key in ["consistency", "relevance", "match"]:
            assert 0 <= result["breakdown"][key] <= 1


class TestConsistencyScore:
    def test_single_result(self, service):
        results = [{"score": 1.0}]
        score = service._calc_consistency(results)
        assert score == 1.0

    def test_uniform_scores(self, service, uniform_results):
        score = service._calc_consistency(uniform_results)
        assert score < 0.01

    def test_skewed_scores(self, service, skewed_results):
        score = service._calc_consistency(skewed_results)
        assert score > 0.5

    def test_all_zero_scores(self, service):
        results = [{"score": 0}, {"score": 0}]
        score = service._calc_consistency(results)
        assert score == 0.0

    def test_empty_results(self, service):
        score = service._calc_consistency([])
        assert score == 1.0

    def test_consistency_range(self, service, sample_results):
        score = service._calc_consistency(sample_results)
        assert 0 <= score <= 1


class TestRelevanceScore:
    def test_perfect_match(self, service):
        results = [
            {"title": "Python装饰器教程", "content": "学习Python装饰器", "snippet": "装饰器是Python特性"},
        ]
        score = service._calc_relevance("Python装饰器", results)
        assert score > 0.5

    def test_no_match(self, service):
        results = [
            {"title": "完全无关的内容", "content": "这里没有任何相关内容", "snippet": "无关"},
        ]
        score = service._calc_relevance("Python装饰器", results)
        assert score < 0.5

    def test_partial_match(self, service):
        results = [
            {"title": "Python basics", "content": "learn Python programming", "snippet": "Python入门"},
        ]
        score = service._calc_relevance("Python decorator", results)
        assert 0 < score <= 1

    def test_empty_query(self, service):
        results = [{"title": "test", "content": "test", "snippet": "test"}]
        score = service._calc_relevance("", results)
        assert score == 0.0

    def test_chinese_query(self, service):
        results = [
            {"title": "装饰器详解", "content": "装饰器是Python的重要特性", "snippet": "装饰器详解"},
        ]
        score = service._calc_relevance("装饰器", results)
        assert score > 0.5

    def test_relevance_range(self, service, sample_results):
        score = service._calc_relevance("Python装饰器", sample_results)
        assert 0 <= score <= 1


class TestContentMatch:
    def test_high_match(self, service):
        results = [
            {"title": "decorator", "content": "Python decorator is a function", "snippet": "详解"},
        ]
        content = "Python decorator"
        score = service._calc_content_match(content, results)
        assert score > 0.3

    def test_low_match(self, service):
        results = [
            {"title": "完全无关", "content": "无关内容", "snippet": "无关"},
        ]
        content = "装饰器是Python的重要特性"
        score = service._calc_content_match(content, results)
        assert score < 0.5

    def test_empty_content(self, service, sample_results):
        score = service._calc_content_match("", sample_results)
        assert score == 0.0

    def test_empty_results(self, service):
        score = service._calc_content_match("test content", [])
        assert score == 0.0

    def test_content_match_range(self, service, sample_results):
        content = "装饰器是Python的重要特性"
        score = service._calc_content_match(content, sample_results)
        assert 0 <= score <= 1

    def test_full_overlap(self, service):
        results = [
            {"title": "装饰器", "content": "装饰器是Python的高级特性", "snippet": "高级"},
        ]
        content = "装饰器是Python的高级特性"
        score = service._calc_content_match(content, results)
        assert score > 0.8


class TestEdgeCases:
    def test_result_missing_fields(self, service):
        results = [{"score": 0.5}]
        result = service.calculate_confidence("test", results)
        assert 0 <= result["score"] <= 100

    def test_result_with_none_values(self, service):
        results = [{"title": "", "content": "", "snippet": "", "score": 0.5}]
        result = service.calculate_confidence("test", results)
        assert 0 <= result["score"] <= 100

    def test_special_characters_in_query(self, service):
        results = [
            {"title": "test", "content": "test content", "snippet": "snippet", "score": 0.5},
        ]
        result = service.calculate_confidence("Python@#$%^&*()", results)
        assert 0 <= result["score"] <= 100

    def test_large_result_set(self, service):
        results = [
            {"title": f"结果{i}", "content": f"内容{i}", "snippet": f"片段{i}", "score": 0.5}
            for i in range(100)
        ]
        result = service.calculate_confidence("测试", results, content="测试内容")
        assert 0 <= result["score"] <= 100
