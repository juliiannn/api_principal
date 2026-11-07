from typing import List, Optional

from app.model import Piar
from app.repository.base_repository import BaseRepository


class PiarRepository(BaseRepository):

    def find_active_by_id(self, piar_id: int) -> Optional[Piar]:
        return self.db.query(Piar).filter(Piar.id == piar_id, Piar.estado.is_(True)).first()

    def find_active_by_student_newest_first(self, student_id: int) -> List[Piar]:
        return (
            self.db.query(Piar).filter(Piar.student_id == student_id, Piar.estado.is_(True))
            .order_by(Piar.school_year.desc()).all()
        )

    def exists_by_student_and_school_year(self, student_id: int, school_year: int) -> bool:
        return self.db.query(Piar).filter(
            Piar.student_id == student_id, Piar.school_year == school_year
        ).first() is not None

    def find_by_id(self, piar_id: int) -> Optional[Piar]:
        """Incluye los PIAR desactivados (para poder reactivarlos)."""
        return self.db.query(Piar).filter(Piar.id == piar_id).first()

    def find_all_newest_first(self) -> List[Piar]:
        """Todos los PIAR, activos e inactivos (la tabla del frontend permite reactivarlos)."""
        return self.db.query(Piar).order_by(Piar.estado.desc(), Piar.creado.desc()).all()
