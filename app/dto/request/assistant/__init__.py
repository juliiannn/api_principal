from typing import List, Literal

from pydantic import Field

from app.dto.camel_model import CamelModel


class AssistantTurn(CamelModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16000)


class AssistantChatRequest(CamelModel):
    """Conversación ya armada por el asistente del frontend (con los datos que el rol puede ver y SIN nombres reales:
    estudiantes y docentes viajan como códigos EST-12 / DOC-3)."""
    messages: List[AssistantTurn] = Field(min_length=1, max_length=14)


__all__ = ["AssistantChatRequest", "AssistantTurn"]
