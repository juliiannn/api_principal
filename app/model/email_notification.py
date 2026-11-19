from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class EmailNotification(AuditMixin, Base):
    """Registro de cada correo que intenta enviar la plataforma (seguimiento y control del administrador)."""
    __tablename__ = "email_notifications"

    id = Column(Integer, primary_key=True, index=True)
    evento = Column(String(40), nullable=False, index=True)            # NotificationEvent
    destinatario = Column(String(255), nullable=False)                  # correo del usuario
    enviado_a = Column(String(255), nullable=True)                      # a dónde salió de verdad (modo prueba)
    asunto = Column(String(255), nullable=False)
    resumen = Column(Text, nullable=False)                              # texto del mensaje (sin adjuntos)
    estado_envio = Column(String(20), nullable=False, index=True)       # NotificationStatus (estado = borrado lógico)
    intentos = Column(Integer, nullable=False, default=0, server_default="0")
    error = Column(Text, nullable=True)
    adjuntos = Column(String(255), nullable=True)                       # ids de report_files separados por coma
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True) # a quién corresponde, si es un usuario
    enviado_en = Column(DateTime, nullable=True)

    user = relationship("User", lazy="selectin")
