from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Role(AuditMixin, Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    users = relationship("User", back_populates="role_ref")
    permissions = relationship("RoleModule", back_populates="role")
