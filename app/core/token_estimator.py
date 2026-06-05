"""轻量级 token 数量估算器。

中英混合场景用启发式方法快速估算，不引入 tiktoken 等重量级依赖。
保守高估（字符数 × 0.45），避免低估导致超出 API 上下文窗口。
"""


class TokenEstimator:
    """Token 估算器"""

    # 保守估算系数：1 字符 ≈ 0.45 token（对中英混合场景略微高估）
    CHAR_COEFFICIENT = 0.45

    # 每条消息的 role/content 格式开销
    FRAMING_OVERHEAD = 20

    @classmethod
    def estimate(cls, text: str) -> int:
        """估算一段文本的 token 数。"""
        if not text:
            return 0
        return max(1, int(len(text) * cls.CHAR_COEFFICIENT))

    @classmethod
    def estimate_messages(cls, messages: list[dict]) -> int:
        """估算 messages 列表的总 token 数。"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += cls.FRAMING_OVERHEAD + cls.estimate(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total += cls.estimate(part["text"])
        return total
