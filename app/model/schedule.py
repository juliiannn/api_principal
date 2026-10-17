from sqlalchemy import Column, Integer, Time, ForeignKey, Index, text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.day_of_week import DayOfWeek
from app.model.audit_mixin import AuditMixin


class Schedule(AuditMixin, Base):
    __tablename__ = "schedules"
    __table_args__ = (Index("uq_schedules_slot", "course_subject_id", "day_of_week", "start_time",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    day_of_week = Column(SqlEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    course_subject = relationship("CourseSubject", back_populates="schedules")
