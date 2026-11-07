from typing import Optional

from app.model import PiarNeed
from app.repository.base_repository import BaseRepository


class PiarNeedRepository(BaseRepository):

    def find_by_piar_and_need(self, piar_id: int, special_need_id: int) -> Optional[PiarNeed]:
        """Busca la necesidad en el PIAR sin filtrar por estado (puede estar desactivada)."""
        return self.db.query(PiarNeed).filter(
            PiarNeed.piar_id == piar_id, PiarNeed.special_need_id == special_need_id
        ).first()

    def find_active_by_piar_and_need(self, piar_id: int, special_need_id: int) -> Optional[PiarNeed]:
        return self.db.query(PiarNeed).filter(
            PiarNeed.piar_id == piar_id, PiarNeed.special_need_id == special_need_id, PiarNeed.estado.is_(True)
        ).first()
