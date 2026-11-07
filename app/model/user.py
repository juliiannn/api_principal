from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.user_role import UserRole
from app.model.document_type import DocumentType
from app.model.gender import Gender
from app.model.audit_mixin import AuditMixin


class User(AuditMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(SqlEnum(DocumentType), nullable=False)
    document = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    address = Column(String, nullable=False)
    password = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    coordinator_profile = relationship("Coordinator", back_populates="user", uselist=False)
    rector_profile = relationship("Rector", back_populates="user", uselist=False)
    role_ref = relationship("Role", back_populates="users", lazy="joined")

    @property
    def role(self) -> UserRole:
        """Compatibilidad: current_user.role.value sigue funcionando. Es de solo lectura;
        para asignar un rol usa role_id."""
        return UserRole(self.role_ref.nombre)
