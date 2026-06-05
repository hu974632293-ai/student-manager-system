"""上下文压缩器 — 基于 token 阈值的二级渐进式压缩。

策略（二级简化）：
- Tier 0（最近 ~2000 token）：保留原始消息完整内容
- Tier 1（超出部分）：合并到会话级 summary（通过 SessionSummarizer 更新）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.core.token_estimator import TokenEstimator

if TYPE_CHECKING:
    from app.services.ai_chat_summarizer import SessionSummarizer

logger = logging.getLogger(__name__)


@dataclass
class CompressedContext:
    """压缩后的上下文结构。"""

    session_summary: str = ""
    recent_messages: list[dict] = field(default_factory=list)  # Tier 0: 原始消息
    summarized_count: int = 0  # 被压缩的消息数
    total_tokens: int = 0
    compression_applied: bool = False


class ContextCompressor:
    """上下文压缩器。

    仅当消息列表总 token 数超过 compression_threshold 时才触发压缩。
    压缩不会调用 LLM，只负责计算要压缩哪些消息，由调用方驱动具体摘要生成。
    """

    def __init__(
        self,
        compression_threshold: int = 4000,
        recent_reserve_tokens: int = 2000,
        summarizer: SessionSummarizer | None = None,
    ):
        self._threshold = max(100, compression_threshold)
        self._recent_reserve = max(200, recent_reserve_tokens)
        self._summarizer = summarizer

    @property
    def threshold(self) -> int:
        return self._threshold

    def needs_compression(self, messages: list[dict]) -> bool:
        """检查是否需要对消息列表进行压缩。"""
        if not messages:
            return False
        total = TokenEstimator.estimate_messages(messages)
        return total > self._threshold

    def compress(
        self,
        messages: list[dict],
        existing_summary: str = "",
        session_summarizer: SessionSummarizer | None = None,
    ) -> CompressedContext:
        """执行上下文压缩。

        Args:
            messages: 按时间升序排列的原始消息列表
            existing_summary: 已有的会话摘要
            session_summarizer: 非空时会对旧消息生成摘要

        Returns:
            CompressedContext 包含压缩后的结果
        """
        summarizer = session_summarizer or self._summarizer
        total_tokens = TokenEstimator.estimate_messages(messages)
        ctx = CompressedContext(
            session_summary=existing_summary,
            total_tokens=total_tokens,
        )

        # 未超阈值，全保留
        if total_tokens <= self._threshold:
            ctx.recent_messages = messages
            return ctx

        # 超阈值：从最新消息向前扫描，保留足够多的最近消息
        accumulated = 0
        split_idx = len(messages)  # 标记最近消息的起始索引

        for i in range(len(messages) - 1, -1, -1):
            msg_tokens = TokenEstimator.estimate_messages([messages[i]])
            if accumulated + msg_tokens <= self._recent_reserve:
                accumulated += msg_tokens
                split_idx = i
            else:
                break

        ctx.recent_messages = messages[split_idx:]
        ctx.compression_applied = True

        # 旧消息处理
        old_messages = messages[:split_idx]
        if old_messages:
            ctx.summarized_count = len(old_messages)

            if summarizer and existing_summary:
                ctx.session_summary = summarizer.update_summary(
                    existing_summary, old_messages
                )
            elif summarizer:
                ctx.session_summary = summarizer.generate_summary(old_messages)
            else:
                # 没有 summarizer 时只做简单计数
                ctx.session_summary = (
                    existing_summary
                    or f"[此会话有 {len(old_messages)} 条已压缩的历史消息]"
                )

        # 重新估算总 token
        recent_tokens = TokenEstimator.estimate_messages(ctx.recent_messages)
        summary_tokens = TokenEstimator.estimate(ctx.session_summary)
        ctx.total_tokens = recent_tokens + summary_tokens

        return ctx
