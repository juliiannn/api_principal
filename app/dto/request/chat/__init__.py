from pydantic import Field

from app.dto.camel_model import CamelModel


class ChatDirectRequest(CamelModel):
    user_id: int = Field(gt=0)


class ChatReadRequest(CamelModel):
    message_id: int = Field(ge=0)


__all__ = ["ChatDirectRequest", "ChatReadRequest"]
