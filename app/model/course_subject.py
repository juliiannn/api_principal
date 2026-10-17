from sqlalchemy import Column, Integer, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class CourseSubject(AuditMixin, Base):
    __tablename__ = "course_subjects"
    __table_args__ = (Index("uq_course_subjects_course_subject", "course_id", "subject_id",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    course = relationship("Course", back_populates="course_subjects")
    subject = relationship("Subject", back_populates="course_subjects")
    teacher = relationship("Teacher", back_populates="course_subjects")
    grades = relationship("Grade", back_populates="course_subject")
    attendances = relationship("Attendance", back_populates="course_subject")
    schedules = relationship("Schedule", back_populates="course_subject")
    assignments = relationship("Assignment", back_populates="course_subject")
