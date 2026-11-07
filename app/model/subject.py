from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Subject(AuditMixin, Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    course_subjects = relationship("CourseSubject", back_populates="subject")
