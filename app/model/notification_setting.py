from sqlalchemy import Boolean, Column, String, Text

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class NotificationSetting(AuditMixin, Base):
    """Configuración de cada evento de notificación: el administrador lo activa o desactiva."""
    __tablename__ = "notification_settings"

    evento = Column(String(40), primary_key=True)        # NotificationEvent
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=False)
    destinatarios = Column(String(255), nullable=False)  # a quién le llega (texto para el administrador)
    activo = Column(Boolean, nullable=False, default=True)
