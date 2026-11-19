"""Notificaciones automáticas ante eventos de la plataforma.

Cada método arma el asunto y el cuerpo del correo y lo encola con NotificationService.notify (envío en segundo
plano, registrado en email_notifications). Se llaman DESPUÉS del commit de la operación y nunca lanzan
excepción: si el correo falla, la nota, la asistencia o el usuario ya quedaron guardados.

Privacidad: los correos no incluyen contraseñas ni diagnósticos del PIAR; solo avisan e invitan a entrar.
"""
import logging
from datetime import date
from typing import Iterable, Optional

from app.config.grade_scale import PASSING_GRADE, fmt
from app.model import Announcement, NotificationEvent, User
from app.repository.notification_repository import EmailNotificationRepository
from app.service.notification_service import NotificationService

log = logging.getLogger("notifications")

LOW_GRADE_LIMIT = PASSING_GRADE   # nota mínima aprobatoria (PASSING_GRADE en el .env)

ROLE_LABELS = {
    "ADMIN": "administrador", "RECTOR": "rector", "COORDINATOR": "coordinador",
    "TEACHER": "docente", "STUDENT": "estudiante",
}


def _safe(fn):
    """Decorador: cualquier error al notificar se registra en el log y no interrumpe la operación."""
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:  # noqa: BLE001
            log.warning("Notificación automática %s no enviada: %s", fn.__name__, e)
            try:
                self.db.rollback()
            except Exception:  # noqa: BLE001
                pass
            return None
    wrapper.__name__ = fn.__name__
    return wrapper


class PlatformNotifier(NotificationService):

    # ---------- cuentas ----------

    @_safe
    def user_registered(self, user: User) -> None:
        role = ROLE_LABELS.get(user.role_ref.nombre if user.role_ref else "", "usuario")
        self.notify(
            NotificationEvent.USER_REGISTERED, user.email, "Bienvenido(a) a la plataforma académica",
            f"Hola {user.full_name}:\n\n"
            f"Se creó tu cuenta en la plataforma académica del colegio con el rol de {role}.\n\n"
            f"Usuario: {user.email}\n"
            "Contraseña inicial: tu número de documento. La plataforma te pedirá cambiarla la primera vez "
            "que inicies sesión.\n\n"
            "Si no reconoces este registro, comunícate con la secretaría del colegio.",
            user.id,
        )

    @_safe
    def password_changed(self, user: User, by_admin: bool) -> None:
        if by_admin:
            body = (f"Hola {user.full_name}:\n\n"
                    "Un administrador restableció la contraseña de tu cuenta. Ahora tu contraseña es tu número de "
                    "documento y deberás cambiarla al iniciar sesión.\n\n"
                    "Si no solicitaste este cambio, comunícate con la secretaría del colegio.")
        else:
            body = (f"Hola {user.full_name}:\n\n"
                    f"La contraseña de tu cuenta se cambió el {date.today():%d/%m/%Y}.\n\n"
                    "Si no fuiste tú, comunícate de inmediato con la secretaría del colegio para bloquear la cuenta.")
        self.notify(NotificationEvent.PASSWORD_CHANGED, user.email, "Aviso de seguridad: cambio de contraseña",
                    body, user.id)

    # ---------- alertas académicas ----------

    @_safe
    def low_grade(self, student_id: int, subject: str, course: str, period, value: float) -> None:
        if value is None or float(value) >= LOW_GRADE_LIMIT:
            return
        user = self.student_user(student_id)
        if user is None:
            return
        period = str(getattr(period, "value", period)).replace("PERIOD_", "")
        self.notify(
            NotificationEvent.LOW_GRADE, user.email, f"Alerta académica: {subject} — periodo {period}",
            f"Hola {user.full_name}:\n\n"
            f"Se registró una nota de {fmt(float(value))} en {subject} ({course}) para el periodo {period}, "
            f"por debajo de la nota mínima aprobatoria ({fmt(LOW_GRADE_LIMIT)}).\n\n"
            "Te recomendamos hablar con tu docente para acordar un plan de mejoramiento.",
            user.id,
        )

    @_safe
    def absence(self, student_id: int, subject: str, course: str, the_date: date) -> None:
        user = self.student_user(student_id)
        if user is None:
            return
        ref = f"{subject} ({course}) el {the_date:%d/%m/%Y}"  # texto que aparece en el cuerpo: evita repetir el aviso
        if EmailNotificationRepository(self.db).exists_today(NotificationEvent.ABSENCE.value, user.email, ref):
            return
        self.notify(
            NotificationEvent.ABSENCE, user.email, f"Inasistencia registrada: {subject}",
            f"Hola {user.full_name}:\n\n"
            f"Se registró tu inasistencia a {ref}.\n\n"
            "Si fue un error o tienes una excusa, preséntala a tu docente o a coordinación.",
            user.id,
        )

    # ---------- comunicados ----------

    @_safe
    def announcement(self, a: Announcement) -> None:
        if not self.is_active(NotificationEvent.ANNOUNCEMENT_PUBLISHED):
            return  # desactivado: no se registran cientos de OMITIDOS
        preview = a.contenido if len(a.contenido) <= 600 else a.contenido[:600] + "…"
        self.notify_many(NotificationEvent.ANNOUNCEMENT_PUBLISHED, self.active_users(),
                         f"Comunicado: {a.titulo}", f"{a.titulo}\n\n{preview}")

    # ---------- PIAR ----------

    @_safe
    def piar_changed(self, student_id: int, change: str, author: Optional[User]) -> None:
        student = self.student_user(student_id)
        if student is None:
            return
        recipients: Iterable[User] = [*self.academic_coordinators(), self.group_director_of_student(student_id)]
        recipients = [u for u in recipients if u is not None and (author is None or u.id != author.id)]
        by = f" por {author.full_name}" if author else ""
        self.notify_many(
            NotificationEvent.PIAR_CHANGED, recipients, f"PIAR actualizado: {student.full_name}",
            f"Se registró un cambio en el PIAR de {student.full_name}{by}:\n\n{change}.\n\n"
            "Ingresa a la plataforma (módulo PIAR) para revisar el detalle.",
        )
