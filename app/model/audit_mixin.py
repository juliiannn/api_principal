from sqlalchemy import Column, Boolean, DateTime, func, text


class AuditMixin:
    """Campos de control en TODAS las tablas.
    estado: True = activo, False = eliminado (borrado lógico).
    creado / actualizado: los gestiona la base de datos (default NOW() y trigger).
    """
    estado = Column(Boolean, nullable=False, default=True, server_default=text("TRUE"))
    creado = Column(DateTime, nullable=False, server_default=func.now())
    actualizado = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
