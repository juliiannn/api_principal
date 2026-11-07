from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Student(AuditMixin, Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    guardian_name = Column(String, nullable=False)
    guardian_phone = Column(String, nullable=False)
    guardian_email = Column(String, nullable=False)

    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    piars = relationship("Piar", back_populates="student")
