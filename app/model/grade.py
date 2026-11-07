from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.period import Period
from app.model.audit_mixin import AuditMixin


class Grade(AuditMixin, Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("student_id", "course_subject_id", "period"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    period = Column(SqlEnum(Period), nullable=False)
    value = Column(Numeric(3, 1), nullable=False)

    student = relationship("Student", back_populates="grades")
    course_subject = relationship("CourseSubject", back_populates="grades")
