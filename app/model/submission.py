from sqlalchemy import Column, Integer, Text, Numeric, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class Submission(AuditMixin, Base):
    """Entrega de una tarea por parte de un estudiante (con la nota y la retroalimentación del docente)."""
    __tablename__ = "submissions"
    __table_args__ = (Index("uq_submissions_assignment_student_active", "assignment_id", "student_id",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    contenido = Column(Text, nullable=False)
    nota = Column(Numeric(3, 1), nullable=True)
    retroalimentacion = Column(Text, nullable=True)
    fecha_calificacion = Column(DateTime, nullable=True)
    calificado_por = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    assignment = relationship("Assignment")
    student = relationship("Student")
    grader = relationship("Teacher")
