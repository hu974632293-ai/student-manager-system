"""会话摘要生成器 — 利用 Qwen API 生成/更新会话摘要。"""

import logging

from app.core.qwen_client import QwenClient

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = (
    "你是一个对话摘要助手。请根据以下对话历史，生成一段简洁的会话摘要（200字以内）。"
    "摘要应包含：对话主题、用户的关键信息或偏好、已完成的讨论要点、未解决的问题。"
    "用中文输出，直接输出摘要内容，不要添加任何前缀或解释。\n\n"
)

UPDATE_PROMPT = (
    "你是一个对话摘要助手。以下是当前会话的已有摘要和新增的对话内容。"
    "请将新增信息合并到已有摘要中，生成更新后的摘要（300字以内）。"
    "保留已有摘要中的关键信息，补充新增内容。"
    "用中文输出，直接输出摘要内容，不要添加任何前缀或解释。\n\n"
)


class SessionSummarizer:
    """会话摘要生成器。

    调用 Qwen API 对对话历史进行语义摘要。
    失败时返回空字符串，不阻断主流程。
    """

    def __init__(self, client: QwenClient):
        self._client = client

    def generate_summary(self, messages: list[dict]) -> str:
        """根据对话消息列表生成首次会话摘要。

        Args:
            messages: [{"role": "user"/"assistant", "content": "..."}, ...]

        Returns:
            摘要文本，失败返回空字符串
        """
        if not messages:
            return ""

        conversation_text = self._format_messages(messages)
        prompt = SUMMARIZE_PROMPT + conversation_text

        try:
            summary = self._client.chat(
                [{"role": "user", "content": prompt}],
                parameters={"max_tokens": 400},
            )
            return summary.strip()
        except Exception as exc:
            logger.error("Failed to generate session summary: %s", exc)
            return ""

    def update_summary(self, existing_summary: str, new_messages: list[dict]) -> str:
        """增量更新已有摘要，合并新消息内容。

        Args:
            existing_summary: 已有的会话摘要
            new_messages: 新增的消息列表

        Returns:
            更新后的摘要，失败返回原有摘要
        """
        if not new_messages:
            return existing_summary

        conversation_text = self._format_messages(new_messages)
        prompt = (
            UPDATE_PROMPT
            + f"=== 已有摘要 ===\n{existing_summary}\n\n"
            + f"=== 新增对话 ===\n{conversation_text}"
        )

        try:
            summary = self._client.chat(
                [{"role": "user", "content": prompt}],
                parameters={"max_tokens": 500},
            )
            return summary.strip()
        except Exception as exc:
            logger.error("Failed to update session summary: %s", exc)
            return existing_summary

    @staticmethod
    def _format_messages(messages: list[dict], max_len: int = 300) -> str:
        """将消息列表格式化为可读文本。"""
        lines = []
        for msg in messages:
            role_label = "用户" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")
            if len(content) > max_len:
                content = content[:max_len] + "..."
            lines.append(f"[{role_label}]: {content}")
        return "\n".join(lines)
