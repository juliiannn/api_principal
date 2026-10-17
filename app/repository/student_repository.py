from typing import List, Optional

from app.model import Student
from app.repository.base_repository import BaseRepository


class StudentRepository(BaseRepository):

    def find_active_by_id(self, student_id: int) -> Optional[Student]:
        return self.db.query(Student).filter(Student.id == student_id, Student.estado.is_(True)).first()

    def find_all_active(self) -> List[Student]:
        return self.db.query(Student).filter(Student.estado.is_(True)).all()

    def find_active_by_user_id(self, user_id: int) -> Optional[Student]:
        return self.db.query(Student).filter(Student.user_id == user_id, Student.estado.is_(True)).first()

    def count_active(self) -> int:
        return self.db.query(Student).filter(Student.estado.is_(True)).count()
