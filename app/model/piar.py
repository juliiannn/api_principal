from datetime import date
from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Piar(AuditMixin, Base):
    __tablename__ = "piars"
    __table_args__ = (UniqueConstraint("student_id", "school_year"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    school_year = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False, default=date.today)
    fecha_fin = Column(Date, nullable=True)
    observaciones = Column(Text, nullable=True)
    consentimiento_acudiente = Column(Boolean, nullable=False, default=False)
    elaborado_por = Column(Integer, ForeignKey("users.id"), nullable=False)

    student = relationship("Student", back_populates="piars")
    author = relationship("User")
    needs = relationship("PiarNeed", back_populates="piar")
    goals = relationship("PiarGoal", back_populates="piar")
    adjustments = relationship("PiarAdjustment", back_populates="piar")
