from datetime import date
from sqlalchemy import Column, Integer, Date, ForeignKey, Index, text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.enrollment_status import EnrollmentStatus
from app.model.audit_mixin import AuditMixin


class Enrollment(AuditMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (Index("uq_enrollments_student_course_active", "student_id", "course_id",
                            unique=True, postgresql_where=text("status = 'ACTIVE' AND estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(Date, nullable=False, default=date.today)
    status = Column(SqlEnum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
