from typing import List, Optional

from app.model import Announcement
from app.repository.base_repository import BaseRepository


class AnnouncementRepository(BaseRepository):

    def find_active_by_id(self, announcement_id: int) -> Optional[Announcement]:
        return self.db.query(Announcement).filter(
            Announcement.id == announcement_id, Announcement.estado.is_(True)
        ).first()

    def find_all_active(self) -> List[Announcement]:
        return (
            self.db.query(Announcement).filter(Announcement.estado.is_(True))
            .order_by(Announcement.creado.desc()).all()
        )
