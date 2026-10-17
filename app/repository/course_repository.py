from typing import List, Optional

from app.model import Course
from app.repository.base_repository import BaseRepository


class CourseRepository(BaseRepository):

    def find_by_id(self, course_id: int, include_inactive: bool = False) -> Optional[Course]:
        q = self.db.query(Course).filter(Course.id == course_id)
        if not include_inactive:
            q = q.filter(Course.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[Course]:
        q = self.db.query(Course)
        if not include_inactive:
            q = q.filter(Course.estado.is_(True))
        return q.all()

    def exists_duplicate(self, name: str, classroom: str, school_year: int, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Course).filter(
            Course.name == name, Course.classroom.ilike(classroom),
            Course.school_year == school_year, Course.estado.is_(True),
        )
        if exclude_id is not None:
            q = q.filter(Course.id != exclude_id)
        return q.first() is not None

    def count_active(self) -> int:
        return self.db.query(Course).filter(Course.estado.is_(True)).count()
