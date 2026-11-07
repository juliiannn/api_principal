from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.education_level import EducationLevel
from app.model.audit_mixin import AuditMixin


class Rector(AuditMixin, Base):
    __tablename__ = "rectors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String, unique=True, nullable=False)
    appointment_date = Column(Date, nullable=False)
    administrative_period = Column(String, nullable=False)
    education_level = Column(SqlEnum(EducationLevel), nullable=False)

    user = relationship("User", back_populates="rector_profile")
