from typing import List, Optional

from app.model import CourseSubject, DayOfWeek, Schedule
from app.repository.base_repository import BaseRepository


class ScheduleRepository(BaseRepository):

    def find_active_by_id(self, schedule_id: int) -> Optional[Schedule]:
        return self.db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.estado.is_(True)).first()

    def find_active_by_course_and_day(self, course_id: int, day: DayOfWeek) -> List[Schedule]:
        return self.db.query(Schedule).join(CourseSubject).filter(
            CourseSubject.course_id == course_id, Schedule.day_of_week == day, Schedule.estado.is_(True)
        ).all()

    def find_active_by_teacher_and_day(self, teacher_id: int, day: DayOfWeek) -> List[Schedule]:
        return self.db.query(Schedule).join(CourseSubject).filter(
            CourseSubject.teacher_id == teacher_id, Schedule.day_of_week == day, Schedule.estado.is_(True)
        ).all()

    def find_active_by_course(self, course_id: int) -> List[Schedule]:
        return self.db.query(Schedule).join(CourseSubject).filter(
            CourseSubject.course_id == course_id, Schedule.estado.is_(True)
        ).all()

    def find_active_by_teacher(self, teacher_id: int) -> List[Schedule]:
        return self.db.query(Schedule).join(CourseSubject).filter(
            CourseSubject.teacher_id == teacher_id, Schedule.estado.is_(True)
        ).all()
