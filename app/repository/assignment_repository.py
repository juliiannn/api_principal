from typing import List, Optional

from app.model import Assignment, CourseSubject
from app.repository.base_repository import BaseRepository


class AssignmentRepository(BaseRepository):

    def find_active_by_course(self, course_id: int) -> List[Assignment]:
        return self.db.query(Assignment).join(CourseSubject).filter(
            CourseSubject.course_id == course_id, Assignment.estado.is_(True), CourseSubject.estado.is_(True)
        ).all()

    def find_active_by_course_subject(self, course_subject_id: int) -> List[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.course_subject_id == course_subject_id, Assignment.estado.is_(True)
        ).all()

    def find_active_by_id(self, assignment_id: int) -> Optional[Assignment]:
        return self.db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.estado.is_(True)).first()

    def find_active_by_teacher(self, teacher_id: int) -> List[Assignment]:
        """Tareas activas de las materias que dicta el docente (más recientes primero)."""
        return (
            self.db.query(Assignment).join(CourseSubject)
            .filter(CourseSubject.teacher_id == teacher_id, Assignment.estado.is_(True),
                    CourseSubject.estado.is_(True))
            .order_by(Assignment.creado.desc()).all()
        )

    def find_all_active(self) -> List[Assignment]:
        return self.db.query(Assignment).filter(Assignment.estado.is_(True)).order_by(Assignment.creado.desc()).all()
