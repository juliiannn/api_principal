from typing import List, Optional

from app.model import Grade, Period
from app.repository.base_repository import BaseRepository


class GradeRepository(BaseRepository):

    def find_active_by_id(self, grade_id: int) -> Optional[Grade]:
        return self.db.query(Grade).filter(Grade.id == grade_id, Grade.estado.is_(True)).first()

    def find_active_by_student(self, student_id: int) -> List[Grade]:
        return self.db.query(Grade).filter(Grade.student_id == student_id, Grade.estado.is_(True)).all()

    def find_active_by_course_subject(self, course_subject_id: int) -> List[Grade]:
        return self.db.query(Grade).filter(
            Grade.course_subject_id == course_subject_id, Grade.estado.is_(True)
        ).all()

    def exists_by_student_course_subject_period(self, student_id: int, course_subject_id: int, period: Period) -> bool:
        return self.db.query(Grade).filter(
            Grade.student_id == student_id, Grade.course_subject_id == course_subject_id, Grade.period == period
        ).first() is not None

    def find_all_active(self) -> List[Grade]:
        return self.db.query(Grade).filter(Grade.estado.is_(True)).all()
