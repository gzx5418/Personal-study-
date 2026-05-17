from __future__ import annotations

import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)


class ConfidenceService:

    def calculate_confidence(
        self,
        query: str,
        results: list[dict],
        content: str = "",
    ) -> dict[str, Any]:
        if not results:
            logger.info("confidence: no results, score=0")
            return {"score": 0, "breakdown": {"consistency": 0, "relevance": 0, "match": 0}}

        consistency = self._calc_consistency(results)
        relevance = self._calc_relevance(query, results)
        match = self._calc_content_match(content, results) if content else 0.0

        score = int(consistency * 30 + relevance * 40 + match * 30)
        score = max(0, min(100, score))

        logger.info(
            "confidence: score=%d, consistency=%.2f, relevance=%.2f, match=%.2f",
            score, consistency, relevance, match,
        )
        return {
            "score": score,
            "breakdown": {
                "consistency": round(consistency, 4),
                "relevance": round(relevance, 4),
                "match": round(match, 4),
            },
        }

    @staticmethod
    def _calc_consistency(results: list[dict]) -> float:
        if len(results) <= 1:
            return 1.0

        scores = [r.get("score", 0) for r in results]
        total = sum(scores)
        if total == 0:
            return 0.0

        probs = [s / total for s in scores]
        entropy = -sum(p * math.log(p + 1e-10) for p in probs if p > 0)
        max_entropy = math.log(len(results))
        if max_entropy <= 0:
            return 1.0
        return max(0.0, 1.0 - entropy / max_entropy)

    @staticmethod
    def _calc_relevance(query: str, results: list[dict]) -> float:
        query_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        if not query_tokens:
            return 0.0

        top_results = results[:3]
        hit_counts = []
        for r in top_results:
            text = (r.get("title", "") + " " + r.get("content", "") + " " + r.get("snippet", "")).lower()
            hits = sum(1 for t in query_tokens if t in text)
            hit_counts.append(hits / len(query_tokens))

        if not hit_counts:
            return 0.0
        return sum(hit_counts) / len(hit_counts)

    @staticmethod
    def _calc_content_match(content: str, results: list[dict]) -> float:
        if not content:
            return 0.0

        content_lower = content.lower()
        content_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', content_lower))
        if not content_tokens:
            return 0.0

        source_tokens: set[str] = set()
        for r in results[:5]:
            text = (r.get("title", "") + " " + r.get("content", "") + " " + r.get("snippet", "")).lower()
            source_tokens.update(re.findall(r'[\w\u4e00-\u9fff]+', text))

        if not source_tokens:
            return 0.0

        overlap = content_tokens & source_tokens
        return len(overlap) / len(content_tokens)


confidence_service = ConfidenceService()
