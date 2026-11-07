from typing import List, Optional

from app.model import Teacher
from app.repository.base_repository import BaseRepository


class TeacherRepository(BaseRepository):

    def find_active_by_id(self, teacher_id: int) -> Optional[Teacher]:
        return self.db.query(Teacher).filter(Teacher.id == teacher_id, Teacher.estado.is_(True)).first()

    def find_all_active(self) -> List[Teacher]:
        return self.db.query(Teacher).filter(Teacher.estado.is_(True)).all()

    def find_active_by_user_id(self, user_id: int) -> Optional[Teacher]:
        return self.db.query(Teacher).filter(Teacher.user_id == user_id, Teacher.estado.is_(True)).first()

    def exists_by_employee_code(self, employee_code: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Teacher).filter(Teacher.employee_code == employee_code)
        if exclude_id is not None:
            q = q.filter(Teacher.id != exclude_id)
        return q.first() is not None

    def count_active(self) -> int:
        return self.db.query(Teacher).filter(Teacher.estado.is_(True)).count()
