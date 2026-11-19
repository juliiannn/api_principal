from typing import List, Optional

from sqlalchemy import func

from app.model import EmailNotification, NotificationSetting, ReportFile
from app.repository.base_repository import BaseRepository


class EmailNotificationRepository(BaseRepository):

    def find_by_id(self, notification_id: int) -> Optional[EmailNotification]:
        return self.db.query(EmailNotification).filter(EmailNotification.id == notification_id).first()

    def search(self, estado: Optional[str], evento: Optional[str], texto: Optional[str], limit: int) -> List[EmailNotification]:
        q = self.db.query(EmailNotification)
        if estado:
            q = q.filter(EmailNotification.estado_envio == estado)
        if evento:
            q = q.filter(EmailNotification.evento == evento)
        if texto:
            like = f"%{texto.strip()}%"
            q = q.filter(EmailNotification.destinatario.ilike(like) | EmailNotification.asunto.ilike(like))
        return q.order_by(EmailNotification.id.desc()).limit(limit).all()

    def count_by_status(self) -> dict[str, int]:
        rows = self.db.query(EmailNotification.estado_envio, func.count()).group_by(EmailNotification.estado_envio).all()
        return {estado: n for estado, n in rows}

    def count_by_event(self) -> dict[str, int]:
        rows = self.db.query(EmailNotification.evento, func.count()).group_by(EmailNotification.evento).all()
        return {evento: n for evento, n in rows}

    def exists_today(self, evento: str, destinatario: str, referencia: str) -> bool:
        """¿Ya se avisó hoy lo mismo a la misma persona? (evita repetir alertas de inasistencia)."""
        return self.db.query(EmailNotification.id).filter(
            EmailNotification.evento == evento,
            EmailNotification.destinatario == destinatario,
            EmailNotification.adjuntos.is_(None),
            func.date(EmailNotification.creado) == func.current_date(),
            EmailNotification.resumen.contains(referencia),
        ).first() is not None


class NotificationSettingRepository(BaseRepository):

    def find_all(self) -> List[NotificationSetting]:
        return self.db.query(NotificationSetting).order_by(NotificationSetting.nombre).all()

    def find(self, evento: str) -> Optional[NotificationSetting]:
        return self.db.query(NotificationSetting).filter(NotificationSetting.evento == evento).first()


class ReportFileRepository(BaseRepository):

    def find_by_id(self, file_id: int) -> Optional[ReportFile]:
        return self.db.query(ReportFile).filter(ReportFile.id == file_id, ReportFile.estado.is_(True)).first()

    def find_recent_by_user(self, user_id: int, now, limit: int = 20) -> List[ReportFile]:
        return (
            self.db.query(ReportFile)
            .filter(ReportFile.usuario_id == user_id, ReportFile.estado.is_(True), ReportFile.expira_en > now)
            .order_by(ReportFile.id.desc()).limit(limit).all()
        )

    def find_expired(self, now) -> List[ReportFile]:
        return self.db.query(ReportFile).filter(ReportFile.estado.is_(True), ReportFile.expira_en <= now).all()
