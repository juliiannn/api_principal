from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.permission_scope import PermissionScope
from app.model.audit_mixin import AuditMixin


class RoleModule(AuditMixin, Base):
    __tablename__ = "role_modules"
    __table_args__ = (UniqueConstraint("role_id", "module_id"),)

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    puede_ver = Column(Boolean, nullable=False, default=False)
    puede_crear = Column(Boolean, nullable=False, default=False)
    puede_editar = Column(Boolean, nullable=False, default=False)
    puede_eliminar = Column(Boolean, nullable=False, default=False)
    alcance = Column(SqlEnum(PermissionScope), nullable=False, default=PermissionScope.ALL)

    role = relationship("Role", back_populates="permissions")
    module = relationship("Module", back_populates="permissions")
