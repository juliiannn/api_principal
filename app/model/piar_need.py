from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class PiarNeed(AuditMixin, Base):
    __tablename__ = "piar_needs"
    __table_args__ = (UniqueConstraint("piar_id", "special_need_id"),)

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    special_need_id = Column(Integer, ForeignKey("special_needs.id"), nullable=False)
    diagnostico = Column(Text, nullable=True)

    piar = relationship("Piar", back_populates="needs")
    special_need = relationship("SpecialNeed", back_populates="piar_needs")
