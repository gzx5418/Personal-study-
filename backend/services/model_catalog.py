from __future__ import annotations

from config import settings


TEXT_MODELS = [
    "deepseek-ai/DeepSeek-V3.2",
    "deepseek-ai/DeepSeek-V3",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen2.5-72B-Instruct",
    "zai-org/GLM-4.6",
    "zai-org/GLM-4.5-Air",
    "moonshotai/Kimi-K2.6",
]

REASONING_MODELS = [
    "Pro/deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-V3.2",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-14B",
    "zai-org/GLM-Z1-32B",
]

VISION_MODELS = [
    "zai-org/GLM-4.6V",
    "zai-org/GLM-4.1V-9B-Thinking",
    "Qwen/Qwen3-VL-32B-Instruct",
    "Qwen/Qwen3-VL-8B-Instruct",
    "Qwen/Qwen2.5-VL-72B-Instruct",
    "deepseek-ai/deepseek-vl2",
]

EMBEDDING_MODELS = [
    "BAAI/bge-m3",
    "Pro/BAAI/bge-m3",
    "Qwen/Qwen3-Embedding-8B",
    "Qwen/Qwen3-Embedding-4B",
    "Qwen/Qwen3-Embedding-0.6B",
    "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-large-en-v1.5",
    "netease-youdao/bce-embedding-base_v1",
]


def get_model_catalog() -> dict:
    return {
        "provider": "siliconflow",
        "text": TEXT_MODELS,
        "reasoning": REASONING_MODELS,
        "vision": VISION_MODELS,
        "embedding": EMBEDDING_MODELS,
        "defaults": {
            "llm_model": settings.LLM_MODEL,
            "reasoning_model": settings.LLM_REASONING_MODEL or settings.LLM_MODEL,
            "vision_model": settings.LLM_VISION_MODEL or settings.LLM_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
    }
