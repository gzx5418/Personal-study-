from __future__ import annotations

import hashlib
import json
import logging
import random
import uuid
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Question:
    id: str
    type: str
    difficulty: str
    content: str
    options: list[str] | None = None
    answer: str = ""
    explanation: str = ""
    knowledge_point: str = ""
    source_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QuestionService:

    QUESTION_TYPES = ("mcq", "judge", "fill", "short_answer", "coding")
    DIFFICULTY_LEVELS = ("easy", "medium", "hard")

    COGNITIVE_MAP = {
        "easy": ["记忆", "理解"],
        "medium": ["应用", "分析"],
        "hard": ["评价", "创造"],
    }

    MASTERY_DISTRIBUTIONS: dict[str, dict[str, float]] = {
        "low": {"easy": 0.7, "medium": 0.3, "hard": 0.0},
        "mid": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
        "high": {"easy": 0.1, "medium": 0.4, "hard": 0.5},
    }

    TYPE_WEIGHTS = {
        "mcq": 0.35,
        "judge": 0.20,
        "fill": 0.25,
        "short_answer": 0.15,
        "coding": 0.05,
    }

    DIFFICULTY_KEYWORDS = {
        "easy": ["什么是", "列举", "定义", "描述", "识别", "下列哪个", "属于"],
        "medium": ["比较", "分析", "解释", "为什么", "区别", "应用", "说明"],
        "hard": ["设计", "评价", "证明", "优化", "推导", "综合", "论述"],
    }

    def __init__(self) -> None:
        self._cache: dict[str, Question] = {}
        self._cache_by_topic: dict[str, list[str]] = {}
        self._llm_service = None

    @property
    def llm_service(self):
        if self._llm_service is None:
            from services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    def _make_cache_key(self, q_type: str, topic: str, difficulty: str, content: str) -> str:
        raw = f"{q_type}:{topic}:{difficulty}:{content}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _cache_question(self, question: Question) -> None:
        self._cache[question.id] = question
        topic = question.knowledge_point
        if topic not in self._cache_by_topic:
            self._cache_by_topic[topic] = []
        self._cache_by_topic[topic].append(question.id)

    def get_cached_question(self, q_type: str, topic: str, difficulty: str, content: str) -> Question | None:
        key = self._make_cache_key(q_type, topic, difficulty, content)
        return self._cache.get(key)

    def get_topic_cache(self, topic: str) -> list[Question]:
        ids = self._cache_by_topic.get(topic, [])
        return [self._cache[qid] for qid in ids if qid in self._cache]

    def clear_cache(self) -> None:
        self._cache.clear()
        self._cache_by_topic.clear()
        logger.info("question cache cleared")

    def _build_cached_content(self, topic: str) -> str:
        cached = self.get_topic_cache(topic)
        if not cached:
            return ""
        return "\n".join(f"- {q.content}" for q in cached)

    async def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.llm_service.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens,
            agent_name="question_service",
        )

    def _parse_json_response(self, text: str) -> dict | list | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        for opener, closer, cls in [("{", "}", dict), ("[", "]", list)]:
            start = text.find(opener)
            end = text.rfind(closer) + 1
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(text[start:end])
                    if isinstance(parsed, cls):
                        return parsed
                except json.JSONDecodeError:
                    pass

        return None

    def _pick_cognitive(self, difficulty: str) -> str:
        return random.choice(self.COGNITIVE_MAP.get(difficulty, ["理解"]))

    async def _generate_mcq(self, topic: str, difficulty: str, count: int = 1) -> list[Question]:
        cached_content = self._build_cached_content(topic)
        cognitive = self._pick_cognitive(difficulty)

        prompt = f"""请生成 {count} 道关于「{topic}」的{difficulty}难度选择题。

要求：
- 认知层次：{cognitive}
- 每题必须有恰好 4 个选项（A/B/C/D），仅 1 个正确答案
- 各选项长度大致均衡，不要让正确选项明显更长或更详细
- 干扰项应反映常见错误理解
- 不要使用"以上都是"、"以上都不是"等选项
- 题目不得与以下已有题目重复：
{cached_content if cached_content else "（暂无）"}

输出 JSON 数组：
[
  {{
    "content": "题目内容",
    "options": ["A选项内容", "B选项内容", "C选项内容", "D选项内容"],
    "answer": "A",
    "explanation": "详细解析，说明正确原因和错误选项的问题",
    "knowledge_point": "知识点名称"
  }}
]
只输出 JSON，不要其他内容。"""

        logger.info("generating mcq: topic=%s, difficulty=%s, count=%d", topic, difficulty, count)
        raw = await self._call_llm(prompt)
        data = self._parse_json_response(raw)

        questions: list[Question] = []
        if isinstance(data, list):
            for item in data:
                q = Question(
                    id=uuid.uuid4().hex[:12],
                    type="mcq",
                    difficulty=difficulty,
                    content=item.get("content", ""),
                    options=item.get("options", []),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                    knowledge_point=item.get("knowledge_point", topic),
                    source_id=item.get("source_id"),
                )
                self._cache_question(q)
                questions.append(q)

        logger.info("mcq generated: %d questions for topic=%s", len(questions), topic)
        return questions

    async def _generate_judge(self, topic: str, difficulty: str, count: int = 1) -> list[Question]:
        cached_content = self._build_cached_content(topic)
        cognitive = self._pick_cognitive(difficulty)

        prompt = f"""请生成 {count} 道关于「{topic}」的{difficulty}难度判断题。

要求：
- 认知层次：{cognitive}
- 答案为"正确"或"错误"
- 提供判断依据，说明为什么对或错
- 正确与错误的题目比例大致均衡
- 题目不得与以下已有题目重复：
{cached_content if cached_content else "（暂无）"}

输出 JSON 数组：
[
  {{
    "content": "题目陈述内容",
    "answer": "正确",
    "explanation": "判断依据",
    "knowledge_point": "知识点名称"
  }}
]
只输出 JSON，不要其他内容。"""

        logger.info("generating judge: topic=%s, difficulty=%s, count=%d", topic, difficulty, count)
        raw = await self._call_llm(prompt)
        data = self._parse_json_response(raw)

        questions: list[Question] = []
        if isinstance(data, list):
            for item in data:
                q = Question(
                    id=uuid.uuid4().hex[:12],
                    type="judge",
                    difficulty=difficulty,
                    content=item.get("content", ""),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                    knowledge_point=item.get("knowledge_point", topic),
                    source_id=item.get("source_id"),
                )
                self._cache_question(q)
                questions.append(q)

        logger.info("judge generated: %d questions for topic=%s", len(questions), topic)
        return questions

    async def _generate_fill(self, topic: str, difficulty: str, count: int = 1) -> list[Question]:
        cached_content = self._build_cached_content(topic)
        cognitive = self._pick_cognitive(difficulty)

        prompt = f"""请生成 {count} 道关于「{topic}」的{difficulty}难度填空题。

要求：
- 认知层次：{cognitive}
- 从知识内容中提取关键概念作为填空位置
- 用 ____ 标记填空位置（每题 1-2 个空）
- 提供多个可接受答案（同义表述、别名等均可接受）
- 题目不得与以下已有题目重复：
{cached_content if cached_content else "（暂无）"}

输出 JSON 数组：
[
  {{
    "content": "题目内容，其中____为填空位置",
    "answer": "标准答案",
    "acceptable_answers": ["标准答案", "可接受答案2", "可接受答案3"],
    "explanation": "解析",
    "knowledge_point": "知识点名称"
  }}
]
只输出 JSON，不要其他内容。"""

        logger.info("generating fill: topic=%s, difficulty=%s, count=%d", topic, difficulty, count)
        raw = await self._call_llm(prompt)
        data = self._parse_json_response(raw)

        questions: list[Question] = []
        if isinstance(data, list):
            for item in data:
                acceptable = item.get("acceptable_answers", [])
                answer_text = item.get("answer", "")
                combined_answer = json.dumps(
                    {"standard": answer_text, "acceptable": acceptable},
                    ensure_ascii=False,
                )
                q = Question(
                    id=uuid.uuid4().hex[:12],
                    type="fill",
                    difficulty=difficulty,
                    content=item.get("content", ""),
                    answer=combined_answer,
                    explanation=item.get("explanation", ""),
                    knowledge_point=item.get("knowledge_point", topic),
                    source_id=item.get("source_id"),
                )
                self._cache_question(q)
                questions.append(q)

        logger.info("fill generated: %d questions for topic=%s", len(questions), topic)
        return questions

    async def _generate_short_answer(self, topic: str, difficulty: str, count: int = 1) -> list[Question]:
        cached_content = self._build_cached_content(topic)
        cognitive = self._pick_cognitive(difficulty)

        prompt = f"""请生成 {count} 道关于「{topic}」的{difficulty}难度简答题。

要求：
- 认知层次：{cognitive}
- 生成开放式问题
- 提供参考答案
- 提供评分标准（满分 10 分的评分要点，每项分值）
- 题目不得与以下已有题目重复：
{cached_content if cached_content else "（暂无）"}

输出 JSON 数组：
[
  {{
    "content": "题目内容",
    "answer": "参考答案",
    "scoring_criteria": [
      {{"point": "评分要点1", "score": 3}},
      {{"point": "评分要点2", "score": 4}},
      {{"point": "评分要点3", "score": 3}}
    ],
    "explanation": "解题思路",
    "knowledge_point": "知识点名称"
  }}
]
只输出 JSON，不要其他内容。"""

        logger.info("generating short_answer: topic=%s, difficulty=%s, count=%d", topic, difficulty, count)
        raw = await self._call_llm(prompt)
        data = self._parse_json_response(raw)

        questions: list[Question] = []
        if isinstance(data, list):
            for item in data:
                criteria = item.get("scoring_criteria", [])
                answer_payload = {
                    "reference_answer": item.get("answer", ""),
                    "scoring_criteria": criteria,
                }
                q = Question(
                    id=uuid.uuid4().hex[:12],
                    type="short_answer",
                    difficulty=difficulty,
                    content=item.get("content", ""),
                    answer=json.dumps(answer_payload, ensure_ascii=False),
                    explanation=item.get("explanation", ""),
                    knowledge_point=item.get("knowledge_point", topic),
                    source_id=item.get("source_id"),
                )
                self._cache_question(q)
                questions.append(q)

        logger.info("short_answer generated: %d questions for topic=%s", len(questions), topic)
        return questions

    def _assess_difficulty(self, question: Question) -> str:
        content = question.content
        scores: dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}

        for level, keywords in self.DIFFICULTY_KEYWORDS.items():
            for kw in keywords:
                if kw in content:
                    scores[level] += 1

        if question.type == "mcq" and question.options:
            opt_count = len(question.options)
            if opt_count <= 4:
                scores["easy"] += 1
            else:
                scores["hard"] += 1

        answer_len = len(question.answer)
        if answer_len > 300:
            scores["hard"] += 2
        elif answer_len > 100:
            scores["medium"] += 1

        concept_count = sum(
            1 for kw in ["原理", "机制", "架构", "算法", "策略", "范式", "模型"]
            if kw in content
        )
        scores["hard"] += concept_count

        if sum(scores.values()) == 0:
            return "medium"

        return max(scores, key=lambda k: scores[k])

    def _get_mastery_distribution(self, mastery_level: float) -> dict[str, float]:
        if mastery_level < 0.4:
            return self.MASTERY_DISTRIBUTIONS["low"]
        if mastery_level <= 0.7:
            return self.MASTERY_DISTRIBUTIONS["mid"]
        return self.MASTERY_DISTRIBUTIONS["high"]

    def _allocate_by_difficulty(self, count: int, distribution: dict[str, float]) -> dict[str, int]:
        easy_n = round(count * distribution.get("easy", 0))
        medium_n = round(count * distribution.get("medium", 0))
        hard_n = count - easy_n - medium_n
        if hard_n < 0:
            hard_n = 0
            medium_n = count - easy_n
        return {"easy": easy_n, "medium": medium_n, "hard": hard_n}

    def _allocate_by_type(self, count: int, question_types: list[str]) -> dict[str, int]:
        weights = {t: self.TYPE_WEIGHTS.get(t, 0) for t in question_types}
        total = sum(weights.values())
        if total <= 0:
            return {t: 0 for t in question_types}

        normalized = {t: w / total for t, w in weights.items()}
        result: dict[str, int] = {}
        remaining = count

        for i, t in enumerate(question_types):
            if i == len(question_types) - 1:
                result[t] = max(0, remaining)
            else:
                n = max(0, round(count * normalized[t]))
                result[t] = n
                remaining -= n

        return result

    async def generate_quiz(
        self,
        topic: str,
        mastery_level: float = 0.5,
        count: int = 5,
        question_types: list[str] | None = None,
    ) -> list[Question]:
        if question_types is None:
            question_types = ["mcq", "judge", "fill", "short_answer"]

        question_types = [t for t in question_types if t in self.QUESTION_TYPES]
        if not question_types:
            question_types = ["mcq"]

        distribution = self._get_mastery_distribution(mastery_level)
        difficulty_counts = self._allocate_by_difficulty(count, distribution)

        logger.info(
            "generate_quiz: topic=%s, mastery=%.2f, count=%d, distribution=%s",
            topic, mastery_level, count, difficulty_counts,
        )

        generators = {
            "mcq": self._generate_mcq,
            "judge": self._generate_judge,
            "fill": self._generate_fill,
            "short_answer": self._generate_short_answer,
        }

        all_questions: list[Question] = []

        for difficulty in self.DIFFICULTY_LEVELS:
            diff_count = difficulty_counts.get(difficulty, 0)
            if diff_count <= 0:
                continue

            type_counts = self._allocate_by_type(diff_count, question_types)

            for q_type, type_count in type_counts.items():
                if type_count <= 0:
                    continue

                generator = generators.get(q_type)
                if generator is None:
                    continue

                try:
                    questions = await generator(topic, difficulty, type_count)
                    all_questions.extend(questions)
                except Exception as e:
                    logger.error("generate %s@%s failed: %s", q_type, difficulty, e)

        random.shuffle(all_questions)

        logger.info("generate_quiz done: %d questions for topic=%s", len(all_questions), topic)
        return all_questions

    async def generate_single(
        self,
        topic: str,
        question_type: str = "mcq",
        difficulty: str = "medium",
    ) -> Question | None:
        generator_map = {
            "mcq": self._generate_mcq,
            "judge": self._generate_judge,
            "fill": self._generate_fill,
            "short_answer": self._generate_short_answer,
        }

        generator = generator_map.get(question_type)
        if generator is None:
            logger.warning("unsupported question type: %s", question_type)
            return None

        try:
            questions = await generator(topic, difficulty, 1)
            return questions[0] if questions else None
        except Exception as e:
            logger.error("generate_single failed: type=%s, error=%s", question_type, e)
            return None

    def get_stats(self) -> dict[str, Any]:
        total = len(self._cache)
        by_type: dict[str, int] = {}
        by_difficulty: dict[str, int] = {}
        for q in self._cache.values():
            by_type[q.type] = by_type.get(q.type, 0) + 1
            by_difficulty[q.difficulty] = by_difficulty.get(q.difficulty, 0) + 1
        return {
            "total_cached": total,
            "by_type": by_type,
            "by_difficulty": by_difficulty,
            "topics": len(self._cache_by_topic),
        }


question_service = QuestionService()
