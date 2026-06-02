from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger("zhixue.rag")


class RAGService:
    """RAG 检索服务 — 支持 LlamaIndex 向量检索和简单文本检索两种模式。"""

    def __init__(self) -> None:
        self._index = None
        self._embed_model = None
        self._initialized = False
        self._simple_kbs: dict[str, dict] = {}
        self._cache_max = 256
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_order: list[str] = []
        self._cache_ttl = 300
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

    @staticmethod
    def _normalize_embedding_base(api_base: str) -> str:
        base = (api_base or "").rstrip("/")
        if base.endswith("/embeddings"):
            return base[:-11]
        return base

    def _resolve_embedding_config(self) -> tuple[str, str, str]:
        from services.llm_service import llm_service

        model = llm_service.get_request_option("embedding_model") or settings.EMBEDDING_MODEL
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        api_base = self._normalize_embedding_base(settings.EMBEDDING_HOST or settings.LLM_HOST)
        return model, api_key, api_base

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        try:
            from llama_index.core import Settings as LlamaSettings
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.core import VectorStoreIndex, StorageContext
            from llama_index.vector_stores.chroma import ChromaVectorStore
            import chromadb

            chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
            self._chroma_client = chroma_client
            self._LlamaSettings = LlamaSettings
            self._OpenAIEmbedding = OpenAIEmbedding
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

        model, api_key, api_base = self._resolve_embedding_config()
        self._embed_model = self._OpenAIEmbedding(
            model=model,
            api_key=api_key,
            api_base=api_base,
        )
        self._LlamaSettings.embed_model = self._embed_model

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
        for course_id, kb_data in target_kbs.items():
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
                        "course_id": course_id,
                        "title": title,
                        "chapter": node.get("chapter", ""),
                        "content": content[:500],
                        "score": score,
                    })

        scored = [item for item in scored if item["score"] >= settings.RAG_MIN_SCORE]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text)
        result = []
        for token in tokens:
            result.append(token)
            if re.match(r'[\u4e00-\u9fff]', token):
                for i in range(len(token) - 1):
                    result.append(token[i:i + 2])
        return result

    def _bm25_search(self, query: str, kb_name: str | None = None, top_k: int = 5) -> list[dict]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        target_kbs = {kb_name: self._simple_kbs[kb_name]} if kb_name and kb_name in self._simple_kbs else self._simple_kbs

        docs = []
        for course_id, kb_data in target_kbs.items():
            for node_id, node in kb_data.items():
                content = node.get("content", "")
                title = node.get("title", "")
                docs.append({
                    "node_id": node_id,
                    "course_id": course_id,
                    "title": title,
                    "chapter": node.get("chapter", ""),
                    "content": content,
                    "tokens": self._tokenize(title + " " + content),
                })

        if not docs:
            return []

        doc_count = len(docs)
        df = defaultdict(int)
        for doc in docs:
            unique_tokens = set(doc["tokens"])
            for token in unique_tokens:
                df[token] += 1

        avg_dl = sum(len(doc["tokens"]) for doc in docs) / doc_count if doc_count > 0 else 1

        k1 = 1.5
        b = 0.75

        scored_docs = []
        for doc in docs:
            score = 0.0
            doc_tokens = doc["tokens"]
            dl = len(doc_tokens)
            tf_counter = Counter(doc_tokens)

            for qt in query_tokens:
                if qt not in df:
                    continue
                tf = tf_counter.get(qt, 0)
                idf = math.log((doc_count - df[qt] + 0.5) / (df[qt] + 0.5) + 1)
                tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
                score += idf * tf_norm

            if score > 0:
                scored_docs.append({
                    "node_id": doc["node_id"],
                    "course_id": doc["course_id"],
                    "title": doc["title"],
                    "chapter": doc["chapter"],
                    "content": doc["content"][:500],
                    "score": score,
                })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

    @staticmethod
    def _merge_results(
        bm25_results: list[dict],
        vector_results: list[dict],
        weights: tuple[float, float] = (0.4, 0.6),
        top_k: int = 5,
    ) -> list[dict]:
        k = 60
        rrf_scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, dict] = {}

        for rank, item in enumerate(bm25_results):
            doc_id = item["node_id"]
            rrf_scores[doc_id] += weights[0] * (1.0 / (k + rank + 1))
            doc_map[doc_id] = item

        for rank, item in enumerate(vector_results):
            doc_id = item.get("source_id") or item.get("node_id", "")
            if not doc_id:
                continue
            rrf_scores[doc_id] += weights[1] * (1.0 / (k + rank + 1))
            if doc_id not in doc_map:
                doc_map[doc_id] = item

        merged = []
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            doc = doc_map[doc_id].copy()
            doc["score"] = rrf_score
            merged.append(doc)

        return merged[:top_k]

    @staticmethod
    def _calculate_confidence(results: list[dict], query: str) -> int:
        if not results:
            return 0

        score_sum = sum(r.get("score", 0) for r in results)
        if score_sum == 0:
            return 0

        normalized = [r.get("score", 0) / score_sum for r in results]
        entropy = -sum(p * math.log(p + 1e-10) for p in normalized if p > 0)
        max_entropy = math.log(len(results)) if len(results) > 1 else 1
        consistency = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0

        top_score = results[0].get("score", 0)
        score_gap = 1.0
        if len(results) > 1:
            second_score = results[1].get("score", 0)
            if top_score > 0:
                score_gap = (top_score - second_score) / top_score

        query_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        relevance_scores = []
        for r in results[:3]:
            content = (r.get("content", "") + " " + r.get("title", "")).lower()
            matched = sum(1 for t in query_tokens if t in content)
            relevance_scores.append(matched / len(query_tokens) if query_tokens else 0)
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

        confidence = (consistency * 30 + score_gap * 30 + avg_relevance * 40)
        return max(0, min(100, int(confidence)))

    def _check_cache_ttl(self) -> None:
        """清理过期缓存条目"""
        current_time = time.time()
        expired = [
            key for key, (timestamp, _) in self._cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired:
            del self._cache[key]
            if key in self._cache_order:
                self._cache_order.remove(key)

    def _get_cache(self, cache_key: str) -> Any | None:
        self._check_cache_ttl()
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                if cache_key in self._cache_order:
                    self._cache_order.remove(cache_key)
                    self._cache_order.append(cache_key)
                return data
            del self._cache[cache_key]
            if cache_key in self._cache_order:
                self._cache_order.remove(cache_key)
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        if len(self._cache) >= self._cache_max and cache_key not in self._cache:
            if self._cache_order:
                evict = self._cache_order.pop(0)
                self._cache.pop(evict, None)
        self._cache[cache_key] = (time.time(), data)
        if cache_key in self._cache_order:
            self._cache_order.remove(cache_key)
        self._cache_order.append(cache_key)

    async def search(
        self,
        query: str,
        kb_name: str = "default",
        top_k: int = 5,
    ) -> dict[str, Any]:
        cache_key = f"{query}:{kb_name}:{top_k}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        bm25_results = self._bm25_search(query, kb_name, top_k * 2)

        vector_results = []
        if self._initialized:
            index = self.get_or_create_index(kb_name)
            if index is not None:
                retriever = index.as_retriever(similarity_top_k=top_k * 2)
                nodes = retriever.retrieve(query)
                for node in nodes:
                    vector_results.append({
                        "source_id": node.node.metadata.get("node_id") if node.node.metadata else "",
                        "node_id": node.node.metadata.get("node_id") if node.node.metadata else "",
                        "course_id": node.node.metadata.get("course_id", kb_name) if node.node.metadata else kb_name,
                        "title": node.node.metadata.get("title", "") if node.node.metadata else "",
                        "chapter": node.node.metadata.get("chapter", "") if node.node.metadata else "",
                        "snippet": node.node.get_content()[:500],
                        "content": node.node.get_content()[:500],
                        "score": float(node.score) if node.score else 0,
                        "metadata": dict(node.node.metadata) if node.node.metadata else {},
                    })

        if vector_results:
            merged = self._merge_results(bm25_results, vector_results, top_k=top_k)
        else:
            merged = bm25_results[:top_k]

        if not merged:
            merged = self._simple_search(query, top_k, kb_name=kb_name)

        sources = []
        citations = []
        for idx, r in enumerate(merged):
            source_id = r.get("source_id") or r.get("node_id", f"src_{idx}")
            source = {
                "source_id": source_id,
                "course_id": r.get("course_id", kb_name),
                "title": r.get("title", ""),
                "chapter": r.get("chapter", ""),
                "snippet": r.get("content", "")[:500],
                "content": f"{r.get('title', '')}（{r.get('chapter', '')}）\n{r.get('content', '')[:500]}",
                "score": r.get("score", 0),
                "metadata": r.get("metadata", {"node_id": source_id}),
            }
            sources.append(source)
            citations.append({
                "id": idx + 1,
                "source_id": source_id,
                "title": r.get("title", ""),
                "course_id": r.get("course_id", kb_name),
                "chapter": r.get("chapter", ""),
            })

        context_text = "\n\n---\n\n".join(s["content"] for s in sources[:3])
        confidence = self._calculate_confidence(merged, query)

        result = {
            "answer": context_text,
            "sources": sources,
            "citations": citations,
            "confidence": confidence,
        }

        self._set_cache(cache_key, result)
        return result

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

    def _get_versions_dir(self) -> str:
        versions_dir = os.path.join(settings.KNOWLEDGE_DIR, "_versions")
        os.makedirs(versions_dir, exist_ok=True)
        return versions_dir

    def _save_version_snapshot(self, kb_name: str, version: int) -> None:
        if kb_name not in self._simple_kbs:
            return
        versions_dir = self._get_versions_dir()
        snapshot_path = os.path.join(versions_dir, f"{kb_name}_v{version}.json")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(self._simple_kbs[kb_name], f, ensure_ascii=False, indent=2)

    def _load_version_snapshot(self, kb_name: str, version: int) -> dict | None:
        versions_dir = self._get_versions_dir()
        snapshot_path = os.path.join(versions_dir, f"{kb_name}_v{version}.json")
        if not os.path.exists(snapshot_path):
            return None
        with open(snapshot_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _persist_kb(self, kb_name: str) -> None:
        if kb_name not in self._simple_kbs:
            return
        filepath = os.path.join(settings.KNOWLEDGE_DIR, f"{kb_name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._simple_kbs[kb_name], f, ensure_ascii=False, indent=2)

    def list_knowledge_bases_detailed(self) -> list[dict]:
        from services.database import db

        result = []
        for kb_name, kb_data in self._simple_kbs.items():
            filepath = os.path.join(settings.KNOWLEDGE_DIR, f"{kb_name}.json")
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            mtime = os.path.getmtime(filepath) if os.path.exists(filepath) else 0
            current_ver = db.get_current_version(kb_name)
            result.append({
                "name": kb_name,
                "version": current_ver["version"] if current_ver else 1,
                "document_count": len(kb_data),
                "last_updated": mtime,
                "size_bytes": file_size,
            })
        return result

    def update_knowledge_base(self, kb_name: str, documents: list[dict], version_note: str = "") -> dict:
        from services.database import db

        if kb_name not in self._simple_kbs:
            self._simple_kbs[kb_name] = {}

        existing = self._simple_kbs[kb_name]
        added = 0
        for doc in documents:
            node_id = doc.get("node_id", f"node_{int(time.time() * 1000)}_{added}")
            existing[node_id] = {
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "chapter": doc.get("chapter", ""),
            }
            added += 1

        self._persist_kb(kb_name)

        version = db.create_kb_version(kb_name, len(existing), version_note or f"增量更新, 新增 {added} 篇文档")
        self._save_version_snapshot(kb_name, version)

        logger.info(f"知识库 {kb_name} 更新完成, 新增 {added} 篇文档, 当前版本 v{version}")
        return {
            "success": True,
            "kb_name": kb_name,
            "version": version,
            "added": added,
            "total_documents": len(existing),
        }

    def get_knowledge_base_version(self, kb_name: str) -> dict | None:
        from services.database import db

        current = db.get_current_version(kb_name)
        if not current:
            return None
        return {
            "kb_name": kb_name,
            "version": current["version"],
            "document_count": current["document_count"],
            "note": current["note"],
            "created_at": current["created_at"],
        }

    def rollback_knowledge_base(self, kb_name: str, target_version: int) -> dict:
        from services.database import db

        snapshot = self._load_version_snapshot(kb_name, target_version)
        if snapshot is None:
            logger.warning(f"知识库 {kb_name} 版本 v{target_version} 快照不存在")
            return {"success": False, "error": f"版本 v{target_version} 快照不存在"}

        self._simple_kbs[kb_name] = snapshot
        self._persist_kb(kb_name)

        db.set_current_version(kb_name, target_version)

        if self._initialized:
            try:
                chroma_collection = self._chroma_client.get_or_create_collection(kb_name)
                chroma_collection.delete(where={})
                index = self.get_or_create_index(kb_name)
                if index:
                    from llama_index.core import Document
                    for node_id, node_data in snapshot.items():
                        doc = Document(
                            text=node_data.get("content", ""),
                            metadata={
                                "node_id": node_id,
                                "title": node_data.get("title", ""),
                                "chapter": node_data.get("chapter", ""),
                                "course_id": kb_name,
                            },
                        )
                        index.insert(doc)
            except Exception as e:
                logger.error(f"知识库 {kb_name} 回滚时重建向量索引失败: {e}")

        logger.info(f"知识库 {kb_name} 已回滚到版本 v{target_version}")
        return {
            "success": True,
            "kb_name": kb_name,
            "version": target_version,
            "document_count": len(snapshot),
        }

    def get_context_for_topic(self, topic: str, kb_name: str = "", max_chars: int = 1500) -> dict[str, Any]:
        results = self._simple_search(topic, top_k=3, kb_name=kb_name or None)
        if not results:
            return {"context": "", "sources": []}
        parts = []
        sources = []
        for r in results:
            snippet = r["content"][:max_chars // len(results)]
            parts.append(f"[{r['course_id']}::{r['node_id']}] {r['title']}（{r['chapter']}）\n{snippet}")
            sources.append({
                "source_id": r["node_id"],
                "course_id": r["course_id"],
                "title": r["title"],
                "chapter": r["chapter"],
                "snippet": snippet,
                "score": r["score"],
            })
        return {"context": "\n\n".join(parts), "sources": sources}


rag_service = RAGService()
