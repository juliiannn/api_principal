from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.model import Teacher, Course, CourseSubject
from app.repository.base_repository import BaseRepository


class CourseRepository(BaseRepository):

    def find_by_id(self, course_id: int, include_inactive: bool = False) -> Optional[Course]:
        q = self.db.query(Course).filter(Course.id == course_id)
        if not include_inactive:
            q = q.filter(Course.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[Course]:
        # el listado de cursos muestra el director de grupo: se carga en bloque (no uno por curso)
        q = self.db.query(Course).options(selectinload(Course.director_teacher).selectinload(Teacher.user))
        if not include_inactive:
            q = q.filter(Course.estado.is_(True))
        return q.order_by(Course.id).all()   # orden de creación: de Párvulo a Undécimo

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

    def find_active_for_teacher(self, teacher_id: int) -> List[Course]:
        """Cursos donde el docente dicta alguna materia o es director de grupo."""
        dicta = self.db.query(CourseSubject.course_id).filter(
            CourseSubject.teacher_id == teacher_id, CourseSubject.estado.is_(True)
        )
        return self.db.query(Course).options(selectinload(Course.director_teacher).selectinload(Teacher.user)).filter(
            Course.estado.is_(True), (Course.id.in_(dicta)) | (Course.director_teacher_id == teacher_id)
        ).order_by(Course.id).all()
