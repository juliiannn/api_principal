from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class PiarGoal(AuditMixin, Base):
    __tablename__ = "piar_goals"

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=True)
    descripcion = Column(Text, nullable=False)

    piar = relationship("Piar", back_populates="goals")
    course_subject = relationship("CourseSubject")
    progress = relationship("PiarProgress", back_populates="goal")
