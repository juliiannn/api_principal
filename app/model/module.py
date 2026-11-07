from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Module(AuditMixin, Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    ruta = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    permissions = relationship("RoleModule", back_populates="module")
