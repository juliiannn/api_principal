from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class ChatParticipant(AuditMixin, Base):
    """Usuario dentro de una conversación y hasta qué mensaje ha leído (para no leídos y «Visto»).
    En la sala general la fila se crea la primera vez que el usuario la abre."""
    __tablename__ = "chat_participants"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_chat_participant"),)

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ultimo_leido_id = Column(Integer, nullable=False, default=0, server_default="0")

    conversation = relationship("ChatConversation", back_populates="participants")
    user = relationship("User", lazy="selectin")
