from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.question_service import Question, QuestionService


class _FakeLLM:
    def __init__(self, response: str = "[]"):
        self._response = response

    async def chat(self, **kwargs):
        return self._response


@pytest.fixture
def question_service():
    service = QuestionService()
    return service


@pytest.fixture
def sample_question():
    return Question(
        id="test_id_123",
        type="mcq",
        difficulty="medium",
        content="Python中什么是装饰器？",
        options=["A. 一种函数", "B. 一种类", "C. 一种模块", "D. 一种变量"],
        answer="A",
        explanation="装饰器是一种接受函数作为参数并返回新函数的函数。",
        knowledge_point="装饰器",
    )


@pytest.fixture
def sample_questions():
    return [
        Question(
            id="q1",
            type="mcq",
            difficulty="easy",
            content="什么是变量？",
            options=["A. 存储数据的容器", "B. 一种函数", "C. 一种循环", "D. 一种类"],
            answer="A",
            explanation="变量是存储数据的容器。",
            knowledge_point="变量",
        ),
        Question(
            id="q2",
            type="judge",
            difficulty="medium",
            content="Python是编译型语言。",
            answer="错误",
            explanation="Python是解释型语言。",
            knowledge_point="Python基础",
        ),
        Question(
            id="q3",
            type="fill",
            difficulty="hard",
            content="设计一个____算法来解决此问题。",
            answer="动态规划",
            explanation="此问题适合用动态规划解决。",
            knowledge_point="算法设计",
        ),
    ]


class TestQuestionModel:
    def test_question_creation(self, sample_question):
        assert sample_question.id == "test_id_123"
        assert sample_question.type == "mcq"
        assert sample_question.difficulty == "medium"
        assert sample_question.content == "Python中什么是装饰器？"
        assert len(sample_question.options) == 4
        assert sample_question.answer == "A"
        assert sample_question.knowledge_point == "装饰器"

    def test_question_to_dict(self, sample_question):
        data = sample_question.to_dict()
        assert data["id"] == "test_id_123"
        assert data["type"] == "mcq"
        assert data["difficulty"] == "medium"
        assert data["content"] == "Python中什么是装饰器？"
        assert data["options"] == ["A. 一种函数", "B. 一种类", "C. 一种模块", "D. 一种变量"]
        assert data["answer"] == "A"

    def test_question_defaults(self):
        q = Question(id="id", type="mcq", difficulty="easy", content="test")
        assert q.options is None
        assert q.answer == ""
        assert q.explanation == ""
        assert q.knowledge_point == ""
        assert q.source_id is None


class TestDifficultyAssessment:
    def test_easy_keywords(self, question_service):
        q = Question(id="id", type="mcq", difficulty="easy", content="什么是变量？请列举变量的类型。")
        result = question_service._assess_difficulty(q)
        assert result == "easy"

    def test_medium_keywords(self, question_service):
        q = Question(id="id", type="mcq", difficulty="medium", content="比较列表和元组的区别，并分析它们的应用场景。")
        result = question_service._assess_difficulty(q)
        assert result in ["medium", "hard"]

    def test_hard_keywords(self, question_service):
        q = Question(id="id", type="short_answer", difficulty="hard", content="设计一个算法来优化此问题，并证明其正确性。请论述其复杂度。")
        result = question_service._assess_difficulty(q)
        assert result == "hard"

    def test_concept_keywords(self, question_service):
        q = Question(id="id", type="mcq", difficulty="medium", content="解释操作系统的架构和算法原理。")
        result = question_service._assess_difficulty(q)
        assert result == "hard"

    def test_answer_length_hard(self, question_service):
        long_answer = "x" * 301
        q = Question(id="id", type="mcq", difficulty="medium", content="普通问题", answer=long_answer)
        result = question_service._assess_difficulty(q)
        assert result == "hard"

    def test_answer_length_medium(self, question_service):
        medium_answer = "x" * 150
        q = Question(id="id", type="mcq", difficulty="medium", content="普通问题", answer=medium_answer)
        result = question_service._assess_difficulty(q)
        assert result in ["medium", "hard"]

    def test_no_keywords_returns_medium(self, question_service):
        q = Question(id="id", type="mcq", difficulty="medium", content="abc xyz")
        result = question_service._assess_difficulty(q)
        assert result == "medium"


class TestMasteryDistribution:
    def test_low_mastery(self, question_service):
        dist = question_service._get_mastery_distribution(0.2)
        assert dist == {"easy": 0.7, "medium": 0.3, "hard": 0.0}

    def test_mid_mastery(self, question_service):
        dist = question_service._get_mastery_distribution(0.5)
        assert dist == {"easy": 0.3, "medium": 0.5, "hard": 0.2}

    def test_high_mastery(self, question_service):
        dist = question_service._get_mastery_distribution(0.8)
        assert dist == {"easy": 0.1, "medium": 0.4, "hard": 0.5}

    def test_boundary_low_mid(self, question_service):
        dist = question_service._get_mastery_distribution(0.4)
        assert dist == {"easy": 0.3, "medium": 0.5, "hard": 0.2}

    def test_boundary_mid_high(self, question_service):
        dist = question_service._get_mastery_distribution(0.7)
        assert dist == {"easy": 0.3, "medium": 0.5, "hard": 0.2}


class TestAllocation:
    def test_allocate_by_difficulty(self, question_service):
        distribution = {"easy": 0.5, "medium": 0.3, "hard": 0.2}
        result = question_service._allocate_by_difficulty(10, distribution)
        assert result["easy"] + result["medium"] + result["hard"] == 10

    def test_allocate_by_difficulty_zero(self, question_service):
        distribution = {"easy": 0.0, "medium": 0.0, "hard": 0.0}
        result = question_service._allocate_by_difficulty(5, distribution)
        total = result["easy"] + result["medium"] + result["hard"]
        assert total == 5

    def test_allocate_by_type(self, question_service):
        question_types = ["mcq", "judge"]
        result = question_service._allocate_by_type(10, question_types)
        total = sum(result.values())
        assert total == 10

    def test_allocate_by_type_single(self, question_service):
        result = question_service._allocate_by_type(5, ["mcq"])
        assert result == {"mcq": 5}

    def test_allocate_by_type_empty(self, question_service):
        result = question_service._allocate_by_type(5, [])
        assert result == {}


class TestQuestionCache:
    def test_cache_question(self, question_service, sample_question):
        question_service._cache_question(sample_question)
        assert sample_question.id in question_service._cache
        assert question_service._cache[sample_question.id] == sample_question

    def test_get_cached_question(self, question_service, sample_question):
        question_service._cache_question(sample_question)
        key = question_service._make_cache_key(
            sample_question.type,
            sample_question.knowledge_point,
            sample_question.difficulty,
            sample_question.content,
        )
        question_service._cache[key] = sample_question
        result = question_service.get_cached_question(
            sample_question.type,
            sample_question.knowledge_point,
            sample_question.difficulty,
            sample_question.content,
        )
        assert result == sample_question

    def test_get_cached_question_miss(self, question_service):
        result = question_service.get_cached_question("mcq", "topic", "easy", "content")
        assert result is None

    def test_get_topic_cache(self, question_service, sample_questions):
        for q in sample_questions:
            question_service._cache_question(q)
        result = question_service.get_topic_cache("变量")
        assert len(result) == 1
        assert result[0].knowledge_point == "变量"

    def test_get_topic_cache_empty(self, question_service):
        result = question_service.get_topic_cache("nonexistent")
        assert result == []

    def test_clear_cache(self, question_service, sample_question):
        question_service._cache_question(sample_question)
        question_service.clear_cache()
        assert len(question_service._cache) == 0
        assert len(question_service._cache_by_topic) == 0

    def test_get_stats(self, question_service, sample_questions):
        for q in sample_questions:
            question_service._cache_question(q)
        stats = question_service.get_stats()
        assert stats["total_cached"] == 3
        assert stats["by_type"]["mcq"] == 1
        assert stats["by_type"]["judge"] == 1
        assert stats["by_type"]["fill"] == 1


class TestJsonParsing:
    def test_parse_valid_json(self, question_service):
        text = '{"key": "value"}'
        result = question_service._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_array(self, question_service):
        text = '[1, 2, 3]'
        result = question_service._parse_json_response(text)
        assert result == [1, 2, 3]

    def test_parse_json_with_surrounding_text(self, question_service):
        text = 'Here is the JSON: {"key": "value"} and some trailing text'
        result = question_service._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_invalid_json(self, question_service):
        text = 'not json at all'
        result = question_service._parse_json_response(text)
        assert result is None


class TestGenerateQuiz:
    @pytest.mark.asyncio
    async def test_generate_quiz_calls_generators(self, question_service):
        mock_response = json.dumps([
            {
                "content": "测试题目",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "解析",
                "knowledge_point": "测试",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        questions = await question_service.generate_quiz(
            topic="测试",
            mastery_level=0.5,
            count=1,
            question_types=["mcq"],
        )
        assert isinstance(questions, list)

    @pytest.mark.asyncio
    async def test_generate_quiz_default_types(self, question_service):
        question_service._llm_service = _FakeLLM("[]")
        questions = await question_service.generate_quiz(topic="测试", count=4)
        assert isinstance(questions, list)

    @pytest.mark.asyncio
    async def test_generate_single_returns_question(self, question_service):
        mock_response = json.dumps([
            {
                "content": "测试题目",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "解析",
                "knowledge_point": "测试",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        q = await question_service.generate_single(topic="测试", question_type="mcq", difficulty="easy")
        assert q is not None
        assert isinstance(q, Question)
        assert q.type == "mcq"

    @pytest.mark.asyncio
    async def test_generate_single_unsupported_type(self, question_service):
        q = await question_service.generate_single(topic="测试", question_type="coding", difficulty="easy")
        assert q is None

    @pytest.mark.asyncio
    async def test_generate_mcq_returns_list(self, question_service):
        mock_response = json.dumps([
            {
                "content": "测试题目",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "解析",
                "knowledge_point": "测试",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        questions = await question_service._generate_mcq("测试", "easy", 1)
        assert len(questions) == 1
        assert questions[0].type == "mcq"

    @pytest.mark.asyncio
    async def test_generate_judge_returns_list(self, question_service):
        mock_response = json.dumps([
            {
                "content": "Python是解释型语言",
                "answer": "正确",
                "explanation": "Python确实是解释型语言",
                "knowledge_point": "Python基础",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        questions = await question_service._generate_judge("Python基础", "easy", 1)
        assert len(questions) == 1
        assert questions[0].type == "judge"

    @pytest.mark.asyncio
    async def test_generate_fill_returns_list(self, question_service):
        mock_response = json.dumps([
            {
                "content": "Python中用____关键字定义函数",
                "answer": "def",
                "acceptable_answers": ["def", "def "],
                "explanation": "Python使用def关键字定义函数",
                "knowledge_point": "Python基础",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        questions = await question_service._generate_fill("Python基础", "easy", 1)
        assert len(questions) == 1
        assert questions[0].type == "fill"

    @pytest.mark.asyncio
    async def test_generate_short_answer_returns_list(self, question_service):
        mock_response = json.dumps([
            {
                "content": "解释什么是闭包",
                "answer": "闭包是引用了自由变量的函数",
                "scoring_criteria": [{"point": "定义正确", "score": 5}],
                "explanation": "闭包的概念",
                "knowledge_point": "Python进阶",
            }
        ])
        question_service._llm_service = _FakeLLM(mock_response)
        questions = await question_service._generate_short_answer("Python进阶", "medium", 1)
        assert len(questions) == 1
        assert questions[0].type == "short_answer"
