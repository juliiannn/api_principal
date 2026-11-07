from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.education_level import EducationLevel
from app.model.contract_type import ContractType
from app.model.audit_mixin import AuditMixin


class Teacher(AuditMixin, Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String, unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    profession = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    education_level = Column(SqlEnum(EducationLevel), nullable=False)
    contract_type = Column(SqlEnum(ContractType), nullable=False)

    user = relationship("User", back_populates="teacher_profile")
    course_subjects = relationship("CourseSubject", back_populates="teacher")
    directed_courses = relationship("Course", back_populates="director_teacher")
