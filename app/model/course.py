from sqlalchemy import Column, Integer, String, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Course(AuditMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (Index("uq_courses_name_classroom_year", "name", "classroom", "school_year",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    classroom = Column(String, nullable=False)
    school_year = Column(Integer, nullable=False)
    director_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    director_teacher = relationship("Teacher", back_populates="directed_courses")
    enrollments = relationship("Enrollment", back_populates="course")
    course_subjects = relationship("CourseSubject", back_populates="course")
