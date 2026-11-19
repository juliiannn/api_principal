"""Seguimiento y control de las notificaciones (panel del administrador)."""
from typing import List, Optional

from fastapi import Depends

from app.exception import InvalidRequestException, ResourceNotFoundException
from app.model import EmailNotification, NotificationEvent, NotificationStatus, User
from app.repository.notification_repository import EmailNotificationRepository, NotificationSettingRepository
from app.dto.response.notification import (
    EmailConfigResponse, NotificationResponse, NotificationSettingResponse, NotificationStatsResponse,
)
from app.service import email_sender
from app.service.notification_service import DEFAULT_SETTINGS, NotificationService

EVENT_NAMES = {e.value: nombre for e, nombre, *_ in DEFAULT_SETTINGS}


class NotificationAdminService:

    def __init__(
        self,
        notification_repository: EmailNotificationRepository = Depends(),
        setting_repository: NotificationSettingRepository = Depends(),
        notification_service: NotificationService = Depends(),
    ):
        self.notifications = notification_repository
        self.settings_repo = setting_repository
        self.notifier = notification_service

    @staticmethod
    def to_response(n: EmailNotification) -> NotificationResponse:
        return NotificationResponse(
            id=n.id, evento=n.evento, evento_nombre=EVENT_NAMES.get(n.evento, n.evento),
            destinatario=n.destinatario, enviado_a=n.enviado_a,
            usuario_nombre=n.user.full_name if n.user else None, asunto=n.asunto, resumen=n.resumen,
            estado=n.estado_envio, intentos=n.intentos or 0, error=n.error, tiene_adjuntos=bool(n.adjuntos),
            creado=n.creado, enviado_en=n.enviado_en,
        )

    def list(self, estado: Optional[str], evento: Optional[str], q: Optional[str], limit: int) -> List[NotificationResponse]:
        return [self.to_response(n) for n in self.notifications.search(estado, evento, q, limit)]

    def stats(self) -> NotificationStatsResponse:
        by_status = self.notifications.count_by_status()
        return NotificationStatsResponse(
            total=sum(by_status.values()),
            enviados=by_status.get(NotificationStatus.ENVIADO.value, 0),
            fallidos=by_status.get(NotificationStatus.FALLIDO.value, 0),
            pendientes=by_status.get(NotificationStatus.PENDIENTE.value, 0),
            omitidos=by_status.get(NotificationStatus.OMITIDO.value, 0),
            por_evento=self.notifications.count_by_event(),
        )

    def config(self) -> EmailConfigResponse:
        return EmailConfigResponse(**email_sender.config_status())

    def settings(self) -> List[NotificationSettingResponse]:
        return [NotificationSettingResponse(evento=s.evento, nombre=s.nombre, descripcion=s.descripcion,
                                            destinatarios=s.destinatarios, activo=s.activo)
                for s in self.settings_repo.find_all()]

    def update_setting(self, evento: str, activo: bool) -> NotificationSettingResponse:
        s = self.settings_repo.find(evento)
        if s is None:
            raise ResourceNotFoundException(f"Notification event {evento} not found")
        s.activo = activo
        self.settings_repo.commit()
        return NotificationSettingResponse(evento=s.evento, nombre=s.nombre, descripcion=s.descripcion,
                                           destinatarios=s.destinatarios, activo=s.activo)

    def retry(self, notification_id: int) -> NotificationResponse:
        n = self.notifications.find_by_id(notification_id)
        if n is None:
            raise ResourceNotFoundException(f"Notification with id {notification_id} not found")
        if n.estado_envio == NotificationStatus.ENVIADO.value:
            raise InvalidRequestException("This notification was already sent")
        return self.to_response(self.notifier.retry(n))

    def send_test(self, user: User) -> NotificationResponse:
        cuerpo = (f"Hola, {user.full_name}.\n\nEste es un correo de prueba enviado desde el panel de notificaciones. "
                  "Si lo recibes, el servidor de correo está bien configurado.")
        n = self.notifier.send_now(NotificationEvent.TEST, user.email, "Correo de prueba", cuerpo, user.id, [])
        return self.to_response(n)
