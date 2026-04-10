from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
