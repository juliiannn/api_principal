from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.period import Period
from app.model.progress_level import ProgressLevel
from app.model.audit_mixin import AuditMixin


class PiarProgress(AuditMixin, Base):
    __tablename__ = "piar_progress"
    __table_args__ = (UniqueConstraint("piar_goal_id", "period"),)

    id = Column(Integer, primary_key=True, index=True)
    piar_goal_id = Column(Integer, ForeignKey("piar_goals.id"), nullable=False)
    period = Column(SqlEnum(Period), nullable=False)
    nivel = Column(SqlEnum(ProgressLevel), nullable=False, default=ProgressLevel.NOT_STARTED)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    goal = relationship("PiarGoal", back_populates="progress")
    teacher = relationship("Teacher")
