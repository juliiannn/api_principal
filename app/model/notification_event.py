import enum


class NotificationEvent(str, enum.Enum):
    """Eventos de la plataforma que pueden generar un correo (se activan o desactivan en notification_settings)."""
    USER_REGISTERED = "USER_REGISTERED"          # registro de usuario
    PASSWORD_CHANGED = "PASSWORD_CHANGED"        # actualización importante de la cuenta
    REPORT_GENERATED = "REPORT_GENERATED"        # reporte enviado al correo
    LOW_GRADE = "LOW_GRADE"                      # alerta académica: nota baja
    ABSENCE = "ABSENCE"                          # alerta académica: inasistencia
    ANNOUNCEMENT_PUBLISHED = "ANNOUNCEMENT_PUBLISHED"  # comunicado institucional
    PIAR_CHANGED = "PIAR_CHANGED"                # cambio en la información monitoreada (PIAR)
    TEST = "TEST"                                # correo de prueba del administrador
