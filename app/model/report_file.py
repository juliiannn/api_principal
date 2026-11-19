from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.model.audit_mixin import AuditMixin


class ReportFile(AuditMixin, Base):
    """Reporte generado (XLSX o PDF), guardado en disco de forma TEMPORAL hasta expira_en."""
    __tablename__ = "report_files"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tipo = Column(String(40), nullable=False)          # notas, asistencia, consolidado, estudiantes, piar
    formato = Column(String(10), nullable=False)       # xlsx | pdf
    titulo = Column(String(200), nullable=False)
    filtros = Column(Text, nullable=False)             # filtros aplicados, en texto legible
    nombre_archivo = Column(String(200), nullable=False)
    ruta = Column(String(400), nullable=False)         # ruta interna en REPORTS_DIR (nombre aleatorio)
    tamano_bytes = Column(Integer, nullable=False)
    filas = Column(Integer, nullable=False)
    expira_en = Column(DateTime, nullable=False)
    enviado_a = Column(String(255), nullable=True)     # correo al que se envió, si se envió

    user = relationship("User", lazy="selectin")
