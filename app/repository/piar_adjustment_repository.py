from typing import Optional

from app.model import PiarAdjustment
from app.repository.base_repository import BaseRepository


class PiarAdjustmentRepository(BaseRepository):

    def find_active_by_id(self, adjustment_id: int) -> Optional[PiarAdjustment]:
        return (
            self.db.query(PiarAdjustment)
            .filter(PiarAdjustment.id == adjustment_id, PiarAdjustment.estado.is_(True))
            .first()
        )
