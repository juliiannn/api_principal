from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class ChatConversation(AuditMixin, Base):
    """Conversación del chat en tiempo real: la sala general o un chat privado entre dos usuarios."""
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(10), nullable=False)  # ChatConversationType: GENERAL | DIRECT
    nombre = Column(String(120), nullable=True)                     # solo la sala general
    clave_directa = Column(String(40), unique=True, nullable=True)  # "idMenor:idMayor" evita chats duplicados
    ultimo_mensaje_en = Column(DateTime, nullable=True, index=True)

    participants = relationship("ChatParticipant", back_populates="conversation", lazy="selectin")
