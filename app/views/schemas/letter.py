from typing import Literal, Optional

from pydantic import BaseModel, Field


LetterRecipient = Literal["luke", "assistant_teacher", "head_teacher"]
OllamaCallMethod = Literal["generate", "chat"]


class LetterGenerateRequest(BaseModel):
    recipient: LetterRecipient
    topic: str = Field(min_length=1, max_length=500)
    method: OllamaCallMethod = "chat"
    tone: Optional[str] = Field(default=None, max_length=100)


class LetterSendRequest(LetterGenerateRequest):
    to_email: str = Field(min_length=3, max_length=254)
    subject: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=8000)
