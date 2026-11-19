import enum


class NotificationStatus(str, enum.Enum):
    """Estado de un correo registrado en email_notifications."""
    PENDIENTE = "PENDIENTE"   # en cola, todavía no se intenta
    ENVIADO = "ENVIADO"       # el servidor SMTP lo aceptó
    FALLIDO = "FALLIDO"       # error al enviar (se puede reintentar)
    OMITIDO = "OMITIDO"       # no se envió: correo sin configurar o evento desactivado
