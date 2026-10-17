from datetime import date as date_type
from typing import List

from app.model import Attendance
from app.repository.base_repository import BaseRepository


class AttendanceRepository(BaseRepository):

    def find_active_by_student(self, student_id: int) -> List[Attendance]:
        return self.db.query(Attendance).filter(
            Attendance.student_id == student_id, Attendance.estado.is_(True)
        ).all()

    def find_active_by_course_subject_and_date(self, course_subject_id: int, the_date: date_type) -> List[Attendance]:
        return self.db.query(Attendance).filter(
            Attendance.course_subject_id == course_subject_id, Attendance.date == the_date,
            Attendance.estado.is_(True),
        ).all()

    def exists_by_student_course_subject_date(
        self, student_id: int, course_subject_id: int, the_date: date_type
    ) -> bool:
        return self.db.query(Attendance).filter(
            Attendance.student_id == student_id, Attendance.course_subject_id == course_subject_id,
            Attendance.date == the_date,
        ).first() is not None

    def find_all_active(self) -> List[Attendance]:
        return self.db.query(Attendance).filter(Attendance.estado.is_(True)).all()
