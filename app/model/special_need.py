from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class SpecialNeed(AuditMixin, Base):
    __tablename__ = "special_needs"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    piar_needs = relationship("PiarNeed", back_populates="special_need")
