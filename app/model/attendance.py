from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.attendance_status import AttendanceStatus
from app.model.audit_mixin import AuditMixin


class Attendance(AuditMixin, Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("student_id", "course_subject_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(SqlEnum(AttendanceStatus), nullable=False)

    student = relationship("Student", back_populates="attendances")
    course_subject = relationship("CourseSubject", back_populates="attendances")
