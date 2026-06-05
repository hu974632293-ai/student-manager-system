"""AI 聊天长期记忆功能单元测试。"""

import numpy as np
import pytest

from app.core.token_estimator import TokenEstimator
from app.services.ai_chat_compressor import ContextCompressor
from app.services.ai_chat_retriever import SemanticRetriever


class TestTokenEstimator:
    """TokenEstimator 基础测试"""

    def test_empty_text(self):
        assert TokenEstimator.estimate("") == 0

    def test_short_text(self):
        assert TokenEstimator.estimate("hello") >= 1

    def test_chinese_text(self):
        t = TokenEstimator.estimate("你好世界")
        assert 1 <= t <= 10

    def test_messages(self):
        msgs = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        total = TokenEstimator.estimate_messages(msgs)
        # 每条消息至少 FRAMING_OVERHEAD(20) + content tokens
        assert total >= 42

    def test_messages_with_list_content(self):
        msgs = [{"role": "user", "content": [{"text": "hello"}, {"text": "world"}]}]
        total = TokenEstimator.estimate_messages(msgs)
        assert total >= 4  # 2 * estimate("hello") ≈ 4


class TestContextCompressor:
    """ContextCompressor 单元测试"""

    def test_no_compression_needed(self):
        comp = ContextCompressor(compression_threshold=99999)
        messages = [{"role": "user", "content": "hi"}]
        assert not comp.needs_compression(messages)

    def test_compression_needed(self):
        comp = ContextCompressor(compression_threshold=20)
        messages = [{"role": "user", "content": "x" * 200}]
        assert comp.needs_compression(messages)

    def test_compress_keeps_recent(self):
        """压缩后至少保留最近的 recent_reserve token 的原始消息。"""
        comp = ContextCompressor(compression_threshold=500, recent_reserve_tokens=200)
        # 10 条消息，总 token > threshold
        messages = [{"role": "user", "content": "x" * 150}] * 10
        ctx = comp.compress(messages)
        assert ctx.compression_applied
        assert len(ctx.recent_messages) > 0
        assert ctx.summarized_count > 0

    def test_compress_no_summarizer(self):
        """没有 summarizer 时压缩不报错。"""
        comp = ContextCompressor(compression_threshold=50, recent_reserve_tokens=20)
        messages = [{"role": "user", "content": "x" * 100}] * 5
        ctx = comp.compress(messages, existing_summary="已有摘要")
        assert ctx.compression_applied
        assert ctx.session_summary == "已有摘要"  # 有 existing 时维持原样

    def test_empty_messages_no_compression(self):
        comp = ContextCompressor(compression_threshold=50)
        assert not comp.needs_compression([])

    def test_threshold_minimum(self):
        """threshold 不会低于 100。"""
        comp = ContextCompressor(compression_threshold=1)
        assert comp.threshold >= 100


class TestSemanticRetriever:
    """SemanticRetriever 单元测试（仅测 numpy 计算，不调 API）"""

    def test_cosine_similarity_identical(self):
        q = np.array([1.0, 0.0], dtype=np.float32)
        c = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        sims = SemanticRetriever._cosine_similarity(q, c)
        assert abs(sims[0] - 1.0) < 1e-6
        assert abs(sims[1] - 0.0) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        q = np.zeros(3, dtype=np.float32)
        c = np.ones((1, 3), dtype=np.float32)
        sims = SemanticRetriever._cosine_similarity(q, c)
        assert abs(sims[0]) < 1e-6  # 零向量归一化后接近 0

    def test_format_context_empty(self):
        result = SemanticRetriever.format_context(None, [])
        assert result == ""

    def test_retrieve_returns_empty_for_blank_query(self):
        retriever = SemanticRetriever.__new__(SemanticRetriever)
        retriever._threshold = 0.0
        result = retriever.retrieve("  ", [], [])
        assert result == []
        result = retriever.retrieve("", [], [])
        assert result == []

    def test_retrieve_no_candidates(self):
        retriever = SemanticRetriever.__new__(SemanticRetriever)
        retriever._top_k = 5
        retriever._threshold = 0.65
        # 无法实际调 embed_query，模拟空候选返回空
        # （正常路径需 mock embed_query，这里测试无候选项时的短路行为）
        query_vectors = [{"message_id": 1, "session_id": "s1",
                          "content_text": "test", "embedding": [1.0, 0.0]}]
        # 传了 message_vectors 但 embed_query 会在没有 mock 时失败 -> logger.warning -> 返回 []
        # 我们只测格式化和较短路径
        messages_short = []
        result = retriever.retrieve("test", messages_short, messages_short)
        assert result == []
