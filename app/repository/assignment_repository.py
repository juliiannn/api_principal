from typing import List

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
