from datetime import datetime
from typing import Dict, List, Optional

from app.dto.camel_model import CamelModel


class NotificationResponse(CamelModel):
    """Un correo registrado: a quién, qué, en qué estado quedó y por qué falló (si falló)."""
    id: int
    evento: str
    evento_nombre: str
    destinatario: str
    enviado_a: Optional[str] = None
    usuario_nombre: Optional[str] = None
    asunto: str
    resumen: str
    estado: str
    intentos: int
    error: Optional[str] = None
    tiene_adjuntos: bool = False
    creado: Optional[datetime] = None
    enviado_en: Optional[datetime] = None


class NotificationSettingResponse(CamelModel):
    evento: str
    nombre: str
    descripcion: str
    destinatarios: str
    activo: bool


class NotificationStatsResponse(CamelModel):
    total: int
    enviados: int
    fallidos: int
    pendientes: int
    omitidos: int
    por_evento: Dict[str, int]


class EmailConfigResponse(CamelModel):
    """Configuración del correo SIN secretos (nunca se devuelve la contraseña)."""
    configured: bool
    host: Optional[str] = None
    port: Optional[int] = None
    security: str
    sender: Optional[str] = None
    redirect_to: Optional[str] = None
    allowed_domains: List[str] = []
