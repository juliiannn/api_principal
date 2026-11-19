"""Notificaciones por correo.

Cada correo queda registrado en email_notifications con su estado (PENDIENTE → ENVIADO / FALLIDO, u OMITIDO),
los intentos y el error, para que el administrador haga seguimiento y reintente los fallidos.

- Las notificaciones automáticas se encolan (PENDIENTE) y se envían en segundo plano, para que guardar una nota
  o crear un usuario no espere al servidor de correo.
- El envío de un reporte es inmediato: quien lo pide ve enseguida si llegó o no.
- Cada evento se puede desactivar en notification_settings; un evento desactivado queda registrado como OMITIDO.
- Ningún error de correo rompe la operación que lo originó.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal, get_db
from app.model import (
    Coordinator, CoordinationArea, Course, EmailNotification, Enrollment, EnrollmentStatus, NotificationEvent,
    NotificationSetting, NotificationStatus, ReportFile, Student, Teacher, User,
)
from app.service import email_sender
from app.service.email_templates import render

log = logging.getLogger("notifications")

# Hilos de envío en segundo plano (dos a la vez es suficiente y no satura el servidor SMTP)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mail")

MAX_ATTEMPTS = 3

# Eventos y su configuración inicial (se crean si no existen; el administrador los activa o desactiva)
DEFAULT_SETTINGS = [
    (NotificationEvent.USER_REGISTERED, "Registro de usuario", "Bienvenida cuando se crea una cuenta en la plataforma.", "El usuario nuevo", True),
    (NotificationEvent.PASSWORD_CHANGED, "Cambio de contraseña", "Aviso de seguridad cuando se cambia o se restablece una contraseña.", "El dueño de la cuenta", True),
    (NotificationEvent.REPORT_GENERATED, "Reporte generado", "Envío del reporte solicitado (Excel o PDF) como archivo adjunto.", "Quien solicita el reporte", True),
    (NotificationEvent.LOW_GRADE, "Alerta académica: nota baja", "Aviso cuando se registra una nota menor a 6.0.", "El estudiante", True),
    (NotificationEvent.ABSENCE, "Alerta académica: inasistencia", "Aviso cuando se registra una ausencia (uno por día y materia).", "El estudiante", True),
    (NotificationEvent.ANNOUNCEMENT_PUBLISHED, "Comunicado publicado", "Aviso de cada comunicado institucional nuevo.", "Todos los usuarios activos", False),
    (NotificationEvent.PIAR_CHANGED, "Cambios en el PIAR", "Aviso cuando se crea o modifica un PIAR, sus metas o su avance.", "Coordinación académica y director de grupo", True),
    (NotificationEvent.TEST, "Correo de prueba", "Correo que envía el administrador para comprobar la configuración.", "El administrador", True),
]


def ensure_default_settings(db: Session) -> None:
    """Crea los eventos que falten en notification_settings (se llama al iniciar la API)."""
    existing = {s.evento for s in db.query(NotificationSetting).all()}
    for evento, nombre, descripcion, destinatarios, activo in DEFAULT_SETTINGS:
        if evento.value not in existing:
            db.add(NotificationSetting(evento=evento.value, nombre=nombre, descripcion=descripcion,
                                       destinatarios=destinatarios, activo=activo))
    db.commit()


def _deliver(notification_id: int) -> None:
    """Envía UN correo registrado y guarda el resultado. Usa su propia sesión (corre en otro hilo)."""
    db = SessionLocal()
    try:
        n = db.query(EmailNotification).filter(EmailNotification.id == notification_id).first()
        if n is None or n.estado_envio == NotificationStatus.ENVIADO.value:
            return
        n.intentos = (n.intentos or 0) + 1
        try:
            attachments = _load_attachments(db, n.adjuntos)
            text, html = render(n.asunto, n.resumen)
            n.enviado_a = email_sender.send_email(n.destinatario, n.asunto, text, html, attachments)
            n.estado_envio = NotificationStatus.ENVIADO.value
            n.error = None
            n.enviado_en = datetime.now()
        except email_sender.EmailNotConfigured as e:
            n.estado_envio = NotificationStatus.OMITIDO.value
            n.error = str(e)
        except Exception as e:  # noqa: BLE001 — cualquier error del servidor queda registrado para reintentar
            n.estado_envio = NotificationStatus.FALLIDO.value
            n.error = f"{type(e).__name__}: {e}"[:1000]
            log.warning("Correo %s falló: %s", notification_id, n.error)
        db.commit()
    finally:
        db.close()


def _load_attachments(db: Session, ids: Optional[str]) -> List[email_sender.Attachment]:
    if not ids:
        return []
    files: List[email_sender.Attachment] = []
    for raw in ids.split(","):
        rf = db.query(ReportFile).filter(ReportFile.id == int(raw)).first()
        if rf is None or not rf.estado or rf.expira_en <= datetime.now() or not os.path.exists(rf.ruta):
            raise FileNotFoundError("El archivo del reporte ya venció o no existe; genera el reporte de nuevo.")
        with open(rf.ruta, "rb") as fh:
            mimetype = "application/pdf" if rf.formato == "pdf" else \
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            files.append(email_sender.Attachment(rf.nombre_archivo, fh.read(), mimetype))
    return files


def resume_pending() -> int:
    """Al iniciar la API: envía los correos que quedaron PENDIENTES (p. ej. si el servidor se reinició)."""
    db = SessionLocal()
    try:
        ids = [n.id for n in db.query(EmailNotification.id).filter(
            EmailNotification.estado_envio == NotificationStatus.PENDIENTE.value).all()]
    finally:
        db.close()
    for i in ids:
        _executor.submit(_deliver, i)
    return len(ids)


class NotificationService:

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # ---------- configuración ----------

    def is_active(self, evento: NotificationEvent) -> bool:
        s = self.db.query(NotificationSetting).filter(NotificationSetting.evento == evento.value).first()
        return bool(s and s.activo)

    # ---------- registrar y enviar ----------

    def notify(self, evento: NotificationEvent, destinatario: Optional[str], asunto: str, cuerpo: str,
               usuario_id: Optional[int] = None) -> Optional[EmailNotification]:
        """Registra el correo y lo envía en segundo plano. Nunca lanza excepción."""
        try:
            if not destinatario or not email_sender.is_valid_address(destinatario):
                return None
            n = self._register(evento, destinatario, asunto, cuerpo, usuario_id)
            if n.estado_envio == NotificationStatus.PENDIENTE.value:
                _executor.submit(_deliver, n.id)
            return n
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo registrar la notificación %s: %s", evento, e)
            self.db.rollback()
            return None

    def notify_many(self, evento: NotificationEvent, users: Iterable[User], asunto: str, cuerpo: str) -> int:
        sent = 0
        for u in {u.id: u for u in users if u is not None}.values():
            if self.notify(evento, u.email, asunto, cuerpo, u.id):
                sent += 1
        return sent

    def send_now(self, evento: NotificationEvent, destinatario: str, asunto: str, cuerpo: str,
                 usuario_id: Optional[int], report_file_ids: List[int]) -> EmailNotification:
        """Envía de inmediato (reportes) y devuelve el registro con su estado final."""
        n = self._register(evento, destinatario, asunto, cuerpo, usuario_id, report_file_ids)
        if n.estado_envio == NotificationStatus.PENDIENTE.value:
            _deliver(n.id)
        self.db.expire_all()
        return self.db.query(EmailNotification).filter(EmailNotification.id == n.id).first()

    def retry(self, n: EmailNotification) -> EmailNotification:
        """Reintenta un correo FALLIDO u OMITIDO (lo envía ya y devuelve el resultado)."""
        n.estado_envio = NotificationStatus.PENDIENTE.value
        n.error = None
        self.db.commit()
        _deliver(n.id)
        self.db.expire_all()
        return self.db.query(EmailNotification).filter(EmailNotification.id == n.id).first()

    def _register(self, evento: NotificationEvent, destinatario: str, asunto: str, cuerpo: str,
                  usuario_id: Optional[int], report_file_ids: Optional[List[int]] = None) -> EmailNotification:
        active = self.is_active(evento)
        n = EmailNotification(
            evento=evento.value, destinatario=destinatario.strip(), asunto=asunto[:250], resumen=cuerpo,
            usuario_id=usuario_id, intentos=0,
            adjuntos=",".join(str(i) for i in report_file_ids) if report_file_ids else None,
            estado_envio=NotificationStatus.PENDIENTE.value if active else NotificationStatus.OMITIDO.value,
            error=None if active else "El evento está desactivado en la configuración de notificaciones.",
        )
        self.db.add(n)
        self.db.commit()
        self.db.refresh(n)
        return n

    # ---------- destinatarios frecuentes ----------

    def academic_coordinators(self) -> List[User]:
        rows = self.db.query(Coordinator).filter(Coordinator.estado.is_(True)).all()
        academic = [c.user for c in rows if c.area == CoordinationArea.ACADEMIC]
        return academic or [c.user for c in rows]

    def group_director_of_student(self, student_id: int) -> Optional[User]:
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id, Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.estado.is_(True),
        ).first()
        if enrollment is None:
            return None
        course = self.db.query(Course).filter(Course.id == enrollment.course_id).first()
        if course is None or course.director_teacher_id is None:
            return None
        teacher = self.db.query(Teacher).filter(Teacher.id == course.director_teacher_id).first()
        return teacher.user if teacher else None

    def student_user(self, student_id: int) -> Optional[User]:
        s = self.db.query(Student).filter(Student.id == student_id).first()
        return s.user if s else None

    def active_users(self) -> List[User]:
        return self.db.query(User).filter(User.estado.is_(True), User.enabled.is_(True)).all()

    def cleanup_old(self, days: int = 90) -> None:
        """Opcional: borra físicamente registros de más de N días (no se usa automáticamente)."""
        limit = datetime.now() - timedelta(days=days)
        self.db.query(EmailNotification).filter(EmailNotification.creado < limit).delete()
        self.db.commit()
