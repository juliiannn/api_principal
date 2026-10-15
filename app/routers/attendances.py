from datetime import date as date_type
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_teacher, require_role
from app.exceptions import DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.models import Attendance, CourseSubject, Enrollment, EnrollmentStatus, Student, Teacher, User
from app.schemas import ApiResponse, AttendanceResponse, CreateAttendanceRequest, CreateBulkAttendanceRequest
from app.utils import ensure_teacher_teaches_course_subject, ensure_teacher_teaches_student

router = APIRouter(prefix="/attendances", tags=["Attendances"])


def to_response(a: Attendance) -> AttendanceResponse:
    return AttendanceResponse(
        id=a.id, student_id=a.student_id, student_name=a.student.user.full_name,
        course_subject_id=a.course_subject_id, subject_name=a.course_subject.subject.name,
        course_name=a.course_subject.course.name, date=a.date, status=a.status,
    )


def check_ownership(cs: CourseSubject, current_teacher: Teacher):
    if cs.teacher_id != current_teacher.id:
        raise ForbiddenOperationException("You can only register attendance for subjects assigned to you")


def validate_assignable(db: Session, student: Student, cs: CourseSubject, the_date: date_type):
    if not cs.estado:
        raise InvalidRequestException("Cannot register attendance for an inactive course-subject assignment")

    enrolled = db.query(Enrollment).filter(
        Enrollment.student_id == student.id, Enrollment.course_id == cs.course_id, Enrollment.status == EnrollmentStatus.ACTIVE,
        Enrollment.estado.is_(True)
    ).first()
    if not enrolled:
        raise InvalidRequestException("Student is not actively enrolled in this course")

    duplicate = db.query(Attendance).filter(
        Attendance.student_id == student.id, Attendance.course_subject_id == cs.id, Attendance.date == the_date
    ).first()
    if duplicate:
        raise DuplicateResourceException("Attendance already registered for this student, subject and date")


@router.post("", response_model=ApiResponse[AttendanceResponse], status_code=201)
def create_attendance(request: CreateAttendanceRequest, db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    student = db.query(Student).filter(Student.id == request.student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

    cs = db.query(CourseSubject).filter(CourseSubject.id == request.course_subject_id).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")

    check_ownership(cs, current_teacher)
    validate_assignable(db, student, cs, request.date)

    attendance = Attendance(student_id=student.id, course_subject_id=cs.id, date=request.date, status=request.status)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return ApiResponse(success=True, message="Attendance registered successfully", data=to_response(attendance))


@router.post("/bulk", response_model=ApiResponse[List[AttendanceResponse]], status_code=201)
def create_bulk_attendance(request: CreateBulkAttendanceRequest, db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    cs = db.query(CourseSubject).filter(CourseSubject.id == request.course_subject_id).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
    check_ownership(cs, current_teacher)

    results = []
    for record in request.records:
        student = db.query(Student).filter(Student.id == record.student_id, Student.estado.is_(True)).first()
        if student is None:
            raise ResourceNotFoundException(f"Student with id {record.student_id} not found")
        validate_assignable(db, student, cs, request.date)
        attendance = Attendance(student_id=student.id, course_subject_id=cs.id, date=request.date, status=record.status)
        db.add(attendance)
        db.flush()
        results.append(attendance)

    db.commit()
    for a in results:
        db.refresh(a)

    return ApiResponse(success=True, message="Attendance registered successfully for the class", data=[to_response(a) for a in results])


@router.get("/me", response_model=ApiResponse[List[AttendanceResponse]])
def get_my_attendance(db: Session = Depends(get_db), current_user: User = Depends(require_role("STUDENT"))):
    student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException("No student profile found for the authenticated user")
    items = db.query(Attendance).filter(Attendance.student_id == student.id, Attendance.estado.is_(True)).all()
    return ApiResponse(success=True, message="Attendance retrieved successfully", data=[to_response(a) for a in items])


@router.get("/student/{student_id}", response_model=ApiResponse[List[AttendanceResponse]])
def get_attendance_by_student(
    student_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    if current_user.role.value == "STUDENT":
        own_student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
        if own_student is None or own_student.id != student_id:
            raise ForbiddenOperationException("You can only view your own attendance")
    elif current_user.role.value == "TEACHER":
        ensure_teacher_teaches_student(db, current_user, student_id)

    items = db.query(Attendance).filter(Attendance.student_id == student_id, Attendance.estado.is_(True)).all()
    return ApiResponse(success=True, message="Attendance retrieved successfully", data=[to_response(a) for a in items])


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[AttendanceResponse]])
def get_attendance_by_course_subject_and_date(
    cs_id: int, date: date_type, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    if current_user.role_ref.nombre == "TEACHER":
        ensure_teacher_teaches_course_subject(db, current_user, cs_id)
    items = db.query(Attendance).filter(Attendance.course_subject_id == cs_id, Attendance.date == date, Attendance.estado.is_(True)).all()
    return ApiResponse(success=True, message="Attendance retrieved successfully", data=[to_response(a) for a in items])
