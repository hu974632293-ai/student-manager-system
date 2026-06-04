from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AiChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class AiChatMemoryCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class AiChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class AiChatResponse(BaseModel):
    session_id: str
    reply: str
    context_message_count: int
    memory_count: int = 0
    saved_memory: Optional[str] = None


class AiChatMemoryOut(BaseModel):
    id: int
    user_id: int
    content: str
    source: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
