from sqlalchemy import Column, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class ChatMessage(AuditMixin, Base):
    """Mensaje del chat. Se guarda antes de repartirlo por WebSocket, así el historial nunca se pierde."""
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_conv_id", "conversation_id", "id"),)

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contenido = Column(Text, nullable=False)

    user = relationship("User", lazy="selectin")
