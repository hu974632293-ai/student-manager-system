"""语义检索器 — 利用 Qwen Embedding 实现跨会话历史记忆检索。

检索流程：
1. 将查询文本向量化（Qwen embed_query）
2. 从 DAO 加载候选消息向量 + 记忆向量
3. numpy 批量计算余弦相似度
4. 过滤 + top-K → 格式化为 system prompt 片段
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import numpy as np

from app.core.qwen_client import QwenClient

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """一条检索结果。"""

    source_type: str  # "message" | "memory"
    source_id: int
    content: str
    similarity: float
    metadata: dict = field(default_factory=dict)


class SemanticRetriever:
    """语义检索器。"""

    def __init__(
        self,
        client: QwenClient,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
    ):
        self._client = client
        self._top_k = max(1, top_k)
        self._threshold = max(0.0, min(1.0, similarity_threshold))

    def retrieve(
        self,
        query: str,
        message_vectors: list[dict],
        memories_with_embedding: list[dict],
    ) -> list[RetrievalResult]:
        """执行语义检索。

        Args:
            query: 用户查询文本
            message_vectors: DAO 返回的消息向量，
                [{message_id, session_id, content_text, embedding}, ...]
            memories_with_embedding: 带 embedding 的记忆列表，
                [{id, content, embedding}, ...]

        Returns:
            按相似度降序排列的检索结果
        """
        if not query.strip():
            return []
        if not message_vectors and not memories_with_embedding:
            return []

        # 向量化查询
        try:
            query_vec = np.array(self._client.embed_query(query), dtype=np.float32)
        except Exception as exc:
            logger.warning("Failed to embed query for retrieval: %s", exc)
            return []

        results: list[RetrievalResult] = []

        # 检索消息向量
        if message_vectors:
            try:
                msg_embeddings = [
                    (json.loads(mv["embedding"]) if isinstance(mv["embedding"], str)
                     else mv["embedding"])
                    for mv in message_vectors
                ]
                msg_vecs = np.array(msg_embeddings, dtype=np.float32)
                sims = self._cosine_similarity(query_vec, msg_vecs)
                for i, sim in enumerate(sims):
                    if sim >= self._threshold:
                        mv = message_vectors[i]
                        results.append(RetrievalResult(
                            source_type="message",
                            source_id=mv["message_id"],
                            content=mv["content_text"],
                            similarity=float(sim),
                            metadata={"session_id": mv.get("session_id", "")},
                        ))
            except Exception as exc:
                logger.warning("Failed to search message vectors: %s", exc)

        # 检索记忆向量
        if memories_with_embedding:
            try:
                mem_embeddings = [
                    (json.loads(m["embedding"]) if isinstance(m["embedding"], str)
                     else m["embedding"])
                    for m in memories_with_embedding
                ]
                # memories_with_embedding 可能为空列表（都无 embedding）
                if mem_embeddings:
                    mem_vecs = np.array(mem_embeddings, dtype=np.float32)
                    sims = self._cosine_similarity(query_vec, mem_vecs)
                    for i, sim in enumerate(sims):
                        if sim >= self._threshold:
                            m = memories_with_embedding[i]
                            results.append(RetrievalResult(
                                source_type="memory",
                                source_id=m["id"],
                                content=m["content"],
                                similarity=float(sim),
                            ))
            except Exception as exc:
                logger.warning("Failed to search memory vectors: %s", exc)

        # 按相似度降序，取 top_k
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[: self._top_k]

    def format_context(self, results: list[RetrievalResult]) -> str:
        """将检索结果格式化为注入上下文 system prompt 片段。"""
        if not results:
            return ""

        lines = ["以下是与当前问题相关的历史信息："]
        for i, r in enumerate(results, 1):
            label = "记忆" if r.source_type == "memory" else "历史对话"
            lines.append(f"{i}. [{label}] {r.content}")
        return "\n".join(lines)

    @staticmethod
    def _cosine_similarity(
        query_vec: np.ndarray, candidates: np.ndarray
    ) -> np.ndarray:
        """批量计算余弦相似度。"""
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        candidate_norms = candidates / (
            np.linalg.norm(candidates, axis=1, keepdims=True) + 1e-8
        )
        return np.dot(candidate_norms, query_norm)
