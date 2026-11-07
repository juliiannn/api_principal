from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Assignment(AuditMixin, Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)

    course_subject = relationship("CourseSubject", back_populates="assignments")
