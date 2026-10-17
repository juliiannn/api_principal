from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from fastapi import Depends

from app.dto.response.statistics import (
    CourseAttendanceRateResponse, CourseStudentCountResponse, GeneralStatisticsResponse,
    SubjectAverageGradeResponse,
)
from app.model import AttendanceStatus
from app.repository.attendance_repository import AttendanceRepository
from app.repository.coordinator_repository import CoordinatorRepository
from app.repository.course_repository import CourseRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.grade_repository import GradeRepository
from app.repository.student_repository import StudentRepository
from app.repository.subject_repository import SubjectRepository
from app.repository.teacher_repository import TeacherRepository

_TWO_DECIMALS = Decimal("0.01")


class StatisticsService:

    def __init__(
        self,
        enrollment_repository: EnrollmentRepository = Depends(),
        grade_repository: GradeRepository = Depends(),
        attendance_repository: AttendanceRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
        coordinator_repository: CoordinatorRepository = Depends(),
        course_repository: CourseRepository = Depends(),
        subject_repository: SubjectRepository = Depends(),
    ):
        self.enrollment_repository = enrollment_repository
        self.grade_repository = grade_repository
        self.attendance_repository = attendance_repository
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository
        self.coordinator_repository = coordinator_repository
        self.course_repository = course_repository
        self.subject_repository = subject_repository

    def get_student_count_by_course(self) -> List[CourseStudentCountResponse]:
        grouped = defaultdict(list)
        for e in self.enrollment_repository.find_all_current():
            grouped[e.course_id].append(e)
        return [
            CourseStudentCountResponse(course_id=course_id, course_name=items[0].course.name, student_count=len(items))
            for course_id, items in grouped.items()
        ]

    def get_average_grades_by_subject(self) -> List[SubjectAverageGradeResponse]:
        grouped = defaultdict(list)
        for g in self.grade_repository.find_all_active():
            grouped[g.course_subject_id].append(g)

        result = []
        for _, items in grouped.items():
            cs = items[0].course_subject
            total = sum(item.value for item in items)
            average = (total / Decimal(len(items))).quantize(_TWO_DECIMALS, rounding=ROUND_HALF_UP)
            result.append(SubjectAverageGradeResponse(
                course_id=cs.course_id, course_name=cs.course.name, subject_id=cs.subject_id,
                subject_name=cs.subject.name, average_grade=average, total_grades=len(items),
            ))
        return result

    def get_attendance_rate_by_course(self) -> List[CourseAttendanceRateResponse]:
        grouped = defaultdict(list)
        for r in self.attendance_repository.find_all_active():
            grouped[r.course_subject.course_id].append(r)

        result = []
        for course_id, items in grouped.items():
            present_count = sum(1 for i in items if i.status == AttendanceStatus.PRESENT)
            rate = (Decimal(present_count) / Decimal(len(items)) * Decimal(100)).quantize(
                _TWO_DECIMALS, rounding=ROUND_HALF_UP
            )
            result.append(CourseAttendanceRateResponse(
                course_id=course_id, course_name=items[0].course_subject.course.name,
                attendance_rate=rate, total_records=len(items),
            ))
        return result

    def get_general_statistics(self) -> GeneralStatisticsResponse:
        return GeneralStatisticsResponse(
            total_students=self.student_repository.count_active(),
            total_teachers=self.teacher_repository.count_active(),
            total_coordinators=self.coordinator_repository.count_active(),
            active_courses=self.course_repository.count_active(),
            total_subjects=self.subject_repository.count_active(),
        )
