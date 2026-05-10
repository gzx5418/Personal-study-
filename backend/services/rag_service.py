from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from config import settings


class RAGService:
    """RAG 检索服务 — 支持 LlamaIndex 向量检索和简单文本检索两种模式。"""

    def __init__(self) -> None:
        self._index = None
        self._embed_model = None
        self._initialized = False
        self._simple_kbs: dict[str, dict] = {}
        self._load_all_simple_kbs()

    def _load_all_simple_kbs(self) -> None:
        if not os.path.exists(settings.KNOWLEDGE_DIR):
            return
        for fname in os.listdir(settings.KNOWLEDGE_DIR):
            if fname.endswith(".json") and fname != "knowledge_graph.json":
                course_id = fname[:-5]
                filepath = os.path.join(settings.KNOWLEDGE_DIR, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    self._simple_kbs[course_id] = json.load(f)

    def _load_simple_kb(self) -> None:
        self._load_all_simple_kbs()

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        try:
            from llama_index.core import Settings as LlamaSettings
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.core import VectorStoreIndex, StorageContext
            from llama_index.vector_stores.chroma import ChromaVectorStore
            import chromadb

            self._embed_model = OpenAIEmbedding(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.EMBEDDING_API_KEY or settings.LLM_API_KEY,
                api_base=settings.EMBEDDING_HOST or settings.LLM_HOST,
            )
            LlamaSettings.embed_model = self._embed_model

            chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
            self._chroma_client = chroma_client
            self._VectorStoreIndex = VectorStoreIndex
            self._StorageContext = StorageContext
            self._ChromaVectorStore = ChromaVectorStore
            self._initialized = True
        except ImportError:
            self._initialized = False

    def get_or_create_index(self, kb_name: str):
        self._ensure_initialized()
        if not self._initialized:
            return None

        chroma_collection = self._chroma_client.get_or_create_collection(kb_name)
        vector_store = self._ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = self._StorageContext.from_defaults(vector_store=vector_store)
        return self._VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )

    def _simple_search(self, query: str, top_k: int = 3, kb_name: str | None = None) -> list[dict]:
        query_lower = query.lower()
        query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))

        target_kbs = {kb_name: self._simple_kbs[kb_name]} if kb_name and kb_name in self._simple_kbs else self._simple_kbs

        scored = []
        for _course_id, kb_data in target_kbs.items():
            for node_id, node in kb_data.items():
                content = node.get("content", "")
                title = node.get("title", "")
                text_lower = (title + " " + content).lower()

                score = 0
                for word in query_words:
                    if word in text_lower:
                        score += 1
                if query_lower in text_lower:
                    score += 5

                if score > 0:
                    scored.append({
                        "node_id": node_id,
                        "title": title,
                        "chapter": node.get("chapter", ""),
                        "content": content[:500],
                        "score": score,
                    })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def search(
        self,
        query: str,
        kb_name: str = "default",
        top_k: int = 5,
    ) -> dict[str, Any]:
        if self._initialized:
            index = self.get_or_create_index(kb_name)
            if index is not None:
                retriever = index.as_retriever(similarity_top_k=top_k)
                nodes = retriever.retrieve(query)

                sources = []
                for node in nodes:
                    sources.append({
                        "content": node.node.get_content()[:500],
                        "score": float(node.score) if node.score else 0,
                        "metadata": dict(node.node.metadata) if node.node.metadata else {},
                    })

                context_text = "\n\n---\n\n".join(s["content"] for s in sources[:3])
                return {"answer": context_text, "sources": sources}

        results = self._simple_search(query, top_k, kb_name=kb_name)
        sources = []
        for r in results:
            sources.append({
                "content": f"{r['title']}（{r['chapter']}）\n{r['content']}",
                "score": r["score"],
                "metadata": {"node_id": r["node_id"], "chapter": r["chapter"]},
            })

        context_text = "\n\n---\n\n".join(s["content"] for s in sources)
        return {"answer": context_text, "sources": sources}

    async def add_documents(self, kb_name: str, file_paths: list[str]) -> dict:
        self._ensure_initialized()
        if not self._initialized:
            return {"success": False, "error": "RAG not available"}

        from llama_index.core import SimpleDirectoryReader

        index = self.get_or_create_index(kb_name)
        for fp in file_paths:
            reader = SimpleDirectoryReader(input_files=[fp])
            docs = reader.load_data()
            for doc in docs:
                index.insert(doc)

        return {"success": True, "count": len(file_paths)}

    def list_knowledge_bases(self) -> list[str]:
        return list(self._simple_kbs.keys())

    def get_context_for_topic(self, topic: str, max_chars: int = 1500) -> str:
        results = self._simple_search(topic, top_k=2)
        if not results:
            return ""
        parts = []
        for r in results:
            parts.append(f"【{r['title']}】{r['content'][:max_chars // len(results)]}")
        return "\n\n".join(parts)


rag_service = RAGService()
