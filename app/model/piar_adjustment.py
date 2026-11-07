from sqlalchemy import Column, Integer, ForeignKey, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.adjustment_type import AdjustmentType
from app.model.audit_mixin import AuditMixin


class PiarAdjustment(AuditMixin, Base):
    __tablename__ = "piar_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=True)
    tipo = Column(SqlEnum(AdjustmentType), nullable=False)
    descripcion = Column(Text, nullable=False)

    piar = relationship("Piar", back_populates="adjustments")
    course_subject = relationship("CourseSubject")
