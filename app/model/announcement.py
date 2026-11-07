from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Announcement(AuditMixin, Base):
    """Comunicado institucional publicado por el rector (o el administrador) para todos los roles."""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)
    publicado_por = Column(Integer, ForeignKey("users.id"), nullable=False)

    author = relationship("User")
