from typing import Optional

from app.dto.camel_model import CamelModel


class AssistantStatusResponse(CamelModel):
    configured: bool
    provider: str
    model: Optional[str] = None


class AssistantChatResponse(CamelModel):
    content: str
    model: str
    provider: str
    total_tokens: Optional[int] = None


__all__ = ["AssistantChatResponse", "AssistantStatusResponse"]
