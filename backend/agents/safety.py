from __future__ import annotations

import json
import logging
import re
from typing import Any

from core.agent import BaseAgent, register_agent
from core.context import UnifiedContext
from core.stream_bus import StreamBus

logger = logging.getLogger(__name__)


@register_agent("safety")
class SafetyAgent(BaseAgent):
    """安全审查 Agent — 对生成内容进行质量校验。
    
    检查生成内容是否存在：
    - 事实性错误（与知识库矛盾）
    - 不当内容
    - 格式问题
    """

    def __init__(self) -> None:
        super().__init__(agent_name="safety_agent", module_name="safety")

    def _verify_against_sources(self, content: str, sources: list[dict]) -> list[dict]:
        source_text = ""
        for s in sources:
            parts = [
                s.get("title", ""),
                s.get("chapter", ""),
                s.get("snippet", ""),
                s.get("content", ""),
            ]
            source_text += " ".join(p for p in parts if p) + " "

        source_text_lower = source_text.lower()
        source_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', source_text_lower))

        claim_patterns = [
            r'(?:定义|是指|指的是|是这样定义的)[：:](.{10,80})',
            r'(?:定理|定律|公式|原理)[：:](.{10,80})',
            r'(?:关键[点概]念?|核心)[是为：:](.{10,80})',
            r'(?:首先|其次|最后)[，,](.{10,80})',
            r'(?:\d+[\.\、])\s*(.{10,80})',
        ]

        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, content)
            claims.extend(m.strip() for m in matches if len(m.strip()) > 5)

        content_lines = content.split('\n')
        for line in content_lines:
            line = line.strip()
            if line.startswith(('#', '##', '###')) and len(line) > 4:
                heading_text = re.sub(r'^#+\s*', '', line)
                if len(heading_text) > 2:
                    claims.append(heading_text)

        verified_claims = []
        seen = set()
        for claim in claims[:20]:
            claim_key = claim[:30]
            if claim_key in seen:
                continue
            seen.add(claim_key)

            claim_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', claim.lower()))
            if not claim_tokens:
                continue

            overlap = claim_tokens & source_tokens
            support_ratio = len(overlap) / len(claim_tokens) if claim_tokens else 0
            is_verified = support_ratio >= 0.3

            verified_claims.append({
                "claim": claim[:100],
                "verified": is_verified,
                "support_ratio": round(support_ratio, 3),
            })

        unverified = [vc for vc in verified_claims if not vc["verified"]]
        if unverified:
            logger.info(
                "source verification: %d/%d claims unverified",
                len(unverified), len(verified_claims),
            )

        return verified_claims

    async def process(self, ctx: UnifiedContext, stream: StreamBus) -> dict[str, Any]:
        stream.stage_start("safety", "正在审查内容...")

        content = ctx.config_overrides.get("content_to_review", "")
        content_type = ctx.config_overrides.get("content_type", "general")
        sources = ctx.config_overrides.get("sources", [])

        prompt = self.load_prompt("review", {
            "content": content,
            "content_type": content_type,
            "sources": json.dumps(sources, ensure_ascii=False, indent=2),
        })

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请审查以上内容的质量和准确性。"},
        ]

        result = await self.call_llm_json(messages, temperature=0.2)

        is_safe = result.get("is_safe", True)
        issues = result.get("issues", [])

        if not is_safe:
            stream.thinking(f"发现 {len(issues)} 个问题")

        stream.result({"is_safe": is_safe, "issues": issues, "suggestions": result.get("suggestions", [])})
        stream.stage_end("safety")
        return result

    async def review_content(self, content: str, content_type: str = "general", sources: list[dict] | None = None) -> dict:
        sources = sources or []
        ctx = UnifiedContext()
        ctx.config_overrides = {
            "content_to_review": content,
            "content_type": content_type,
            "sources": sources,
        }
        stream = StreamBus()
        result = await self.process(ctx, stream)

        verified_claims = self._verify_against_sources(content, sources)

        from services.confidence_service import confidence_service
        confidence_info = confidence_service.calculate_confidence(content_type, sources, content)
        confidence = confidence_info["score"]

        total_claims = len(verified_claims)
        verified_count = sum(1 for vc in verified_claims if vc["verified"])
        claim_verification_rate = verified_count / total_claims if total_claims > 0 else 1.0

        if claim_verification_rate < 0.5 and total_claims > 0:
            existing_issues = result.get("issues", [])
            existing_issues.append({
                "type": "unverified_claims",
                "detail": f"{total_claims - verified_count}/{total_claims} 条关键声明未找到知识库来源支撑",
                "severity": "warning",
            })
            result["issues"] = existing_issues
            result["is_safe"] = result.get("is_safe", True) and True
            logger.warning(
                "claim verification low: %d/%d verified",
                verified_count, total_claims,
            )

        result["confidence"] = confidence
        result["confidence_breakdown"] = confidence_info.get("breakdown", {})
        result["verified_claims"] = verified_claims
        result["claim_verification_rate"] = round(claim_verification_rate, 3)

        logger.info(
            "review_content done: is_safe=%s, confidence=%d, claims=%d/%d verified",
            result.get("is_safe"), confidence, verified_count, total_claims,
        )
        return result
