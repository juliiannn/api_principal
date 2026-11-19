from datetime import datetime
from typing import List, Optional

from app.dto.camel_model import CamelModel


class ChatUserResponse(CamelModel):
    """Usuario visible en el chat (sin correo ni datos sensibles)."""
    id: int
    full_name: str
    role: str
    online: bool = False


class ChatMessageResponse(CamelModel):
    id: int
    conversation_id: int
    sender: ChatUserResponse
    content: str
    created_at: datetime


class ChatConversationResponse(CamelModel):
    id: int
    type: str                                   # GENERAL | DIRECT
    name: str                                   # "Sala general" o el nombre de la otra persona
    other_user: Optional[ChatUserResponse] = None
    last_message: Optional[ChatMessageResponse] = None
    unread: int = 0
    last_read_id: int = 0
    other_last_read_id: int = 0                 # para mostrar «Visto» en los chats privados
    online_count: int = 0                       # solo la sala general


__all__ = ["ChatConversationResponse", "ChatMessageResponse", "ChatUserResponse"]
