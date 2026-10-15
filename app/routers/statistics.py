from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Attendance, AttendanceStatus, Coordinator, Course, Enrollment, EnrollmentStatus, Grade, Student, Subject, Teacher, User
from app.schemas import ApiResponse, CourseAttendanceRateResponse, CourseStudentCountResponse, GeneralStatisticsResponse, SubjectAverageGradeResponse

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/students-by-course", response_model=ApiResponse[List[CourseStudentCountResponse]])
def get_student_count_by_course(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR"))):
    enrollments = db.query(Enrollment).filter(
        Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)
    ).all()
    grouped = defaultdict(list)
    for e in enrollments:
        grouped[e.course_id].append(e)

    result = [
        CourseStudentCountResponse(course_id=course_id, course_name=items[0].course.name, student_count=len(items))
        for course_id, items in grouped.items()
    ]
    return ApiResponse(success=True, message="Student count by course retrieved successfully", data=result)


@router.get("/average-grades", response_model=ApiResponse[List[SubjectAverageGradeResponse]])
def get_average_grades_by_subject(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR"))):
    grades = db.query(Grade).filter(Grade.estado.is_(True)).all()
    grouped = defaultdict(list)
    for g in grades:
        grouped[g.course_subject_id].append(g)

    result = []
    for cs_id, items in grouped.items():
        cs = items[0].course_subject
        total = sum(item.value for item in items)
        average = (total / Decimal(len(items))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append(SubjectAverageGradeResponse(
            course_id=cs.course_id, course_name=cs.course.name, subject_id=cs.subject_id,
            subject_name=cs.subject.name, average_grade=average, total_grades=len(items),
        ))
    return ApiResponse(success=True, message="Average grades retrieved successfully", data=result)


@router.get("/attendance-rate", response_model=ApiResponse[List[CourseAttendanceRateResponse]])
def get_attendance_rate_by_course(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR"))):
    records = db.query(Attendance).filter(Attendance.estado.is_(True)).all()
    grouped = defaultdict(list)
    for r in records:
        grouped[r.course_subject.course_id].append(r)

    result = []
    for course_id, items in grouped.items():
        present_count = sum(1 for i in items if i.status == AttendanceStatus.PRESENT)
        rate = (Decimal(present_count) / Decimal(len(items)) * Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append(CourseAttendanceRateResponse(course_id=course_id, course_name=items[0].course_subject.course.name, attendance_rate=rate, total_records=len(items)))
    return ApiResponse(success=True, message="Attendance rate retrieved successfully", data=result)


@router.get("/general", response_model=ApiResponse[GeneralStatisticsResponse])
def get_general_statistics(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR"))):
    data = GeneralStatisticsResponse(
        total_students=db.query(Student).filter(Student.estado.is_(True)).count(),
        total_teachers=db.query(Teacher).filter(Teacher.estado.is_(True)).count(),
        total_coordinators=db.query(Coordinator).filter(Coordinator.estado.is_(True)).count(),
        active_courses=db.query(Course).filter(Course.estado.is_(True)).count(),
        total_subjects=db.query(Subject).filter(Subject.estado.is_(True)).count(),
    )
    return ApiResponse(success=True, message="General statistics retrieved successfully", data=data)
