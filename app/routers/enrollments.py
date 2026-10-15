from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, InvalidStatusTransitionException, ResourceNotFoundException
from app.models import Course, CourseSubject, Enrollment, EnrollmentStatus, Student, Teacher, User
from app.schemas import ApiResponse, CreateEnrollmentRequest, EnrollmentResponse, StudentResponse, TransferEnrollmentRequest, UpdateEnrollmentStatusRequest

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])

VALID_TRANSITIONS = {
    EnrollmentStatus.ACTIVE: {EnrollmentStatus.CANCELLED, EnrollmentStatus.COMPLETED},
    EnrollmentStatus.CANCELLED: set(),
    EnrollmentStatus.COMPLETED: set(),
}


def to_response(e: Enrollment) -> EnrollmentResponse:
    return EnrollmentResponse(
        id=e.id, student_id=e.student_id, student_name=e.student.user.full_name,
        course_id=e.course_id, course_name=e.course.name,
        enrollment_date=e.enrollment_date, status=e.status,
    )


def find_or_404(db: Session, enrollment_id: int) -> Enrollment:
    e = db.query(Enrollment).filter(Enrollment.id == enrollment_id, Enrollment.estado.is_(True)).first()
    if e is None:
        raise ResourceNotFoundException(f"Enrollment with id {enrollment_id} not found")
    return e


def change_status(enrollment: Enrollment, new_status: EnrollmentStatus):
    if enrollment.status == new_status:
        return
    if new_status not in VALID_TRANSITIONS.get(enrollment.status, set()):
        raise InvalidStatusTransitionException(f"Cannot change enrollment status from {enrollment.status.value} to {new_status.value}")
    enrollment.status = new_status


@router.post("", response_model=ApiResponse[EnrollmentResponse], status_code=201)
def create_enrollment(request: CreateEnrollmentRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COORDINATOR"))):
    student = db.query(Student).filter(Student.id == request.student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

    course = db.query(Course).filter(Course.id == request.course_id).first()
    if course is None:
        raise ResourceNotFoundException(f"Course with id {request.course_id} not found")
    if not course.estado:
        raise InvalidRequestException("Cannot enroll a student in an inactive course")

    already = db.query(Enrollment).filter(
        Enrollment.student_id == student.id, Enrollment.course_id == course.id, Enrollment.status == EnrollmentStatus.ACTIVE,
        Enrollment.estado.is_(True)
    ).first()
    if already:
        raise DuplicateResourceException("Student already enrolled in this course")

    enrollment = Enrollment(student_id=student.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return ApiResponse(success=True, message="Enrollment created successfully", data=to_response(enrollment))


@router.put("/transfer", response_model=ApiResponse[EnrollmentResponse])
def transfer_student(request: TransferEnrollmentRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COORDINATOR"))):
    student = db.query(Student).filter(Student.id == request.student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

    current = db.query(Enrollment).filter(
        Enrollment.student_id == student.id, Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)
    ).first()
    if current is None:
        raise ResourceNotFoundException("Student has no active enrollment to transfer from")

    new_course = db.query(Course).filter(Course.id == request.new_course_id).first()
    if new_course is None:
        raise ResourceNotFoundException(f"Course with id {request.new_course_id} not found")
    if not new_course.estado:
        raise InvalidRequestException("Cannot enroll a student in an inactive course")
    if current.course_id == new_course.id:
        raise InvalidRequestException("Student is already enrolled in that course")

    already = db.query(Enrollment).filter(
        Enrollment.student_id == student.id, Enrollment.course_id == new_course.id, Enrollment.status == EnrollmentStatus.ACTIVE,
        Enrollment.estado.is_(True)
    ).first()
    if already:
        raise DuplicateResourceException("Student already enrolled in the target course")

    change_status(current, EnrollmentStatus.CANCELLED)
    db.add(current)

    new_enrollment = Enrollment(student_id=student.id, course_id=new_course.id)
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return ApiResponse(success=True, message="Student transferred successfully", data=to_response(new_enrollment))


@router.get("", response_model=ApiResponse[List[EnrollmentResponse]])
def get_all_enrollments(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    items = db.query(Enrollment).filter(Enrollment.estado.is_(True)).all()
    return ApiResponse(success=True, message="Enrollments retrieved successfully", data=[to_response(i) for i in items])


@router.get("/{enrollment_id}", response_model=ApiResponse[EnrollmentResponse])
def get_enrollment_by_id(enrollment_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    return ApiResponse(success=True, message="Enrollment retrieved successfully", data=to_response(find_or_404(db, enrollment_id)))


@router.get("/course/{course_id}/students", response_model=ApiResponse[List[StudentResponse]])
def get_students_by_course(
    course_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise ResourceNotFoundException(f"Course with id {course_id} not found")

    if current_user.role.value == "TEACHER":
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id, Teacher.estado.is_(True)).first()
        teaches_here = db.query(CourseSubject).filter(
            CourseSubject.course_id == course_id, CourseSubject.teacher_id == teacher.id, CourseSubject.estado.is_(True)
        ).first()
        if not teaches_here:
            raise ForbiddenOperationException("You can only view students from courses where you teach")

    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == course_id, Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)
    ).all()
    students = [
        StudentResponse(
            id=e.student.id, user_id=e.student.user.id, document=e.student.user.document,
            full_name=e.student.user.full_name, email=e.student.user.email, phone=e.student.user.phone,
            birth_date=e.student.user.birth_date, enabled=e.student.user.enabled,
            guardian_name=e.student.guardian_name, guardian_phone=e.student.guardian_phone,
            guardian_email=e.student.guardian_email,
        )
        for e in enrollments
    ]
    return ApiResponse(success=True, message="Students retrieved successfully", data=students)


@router.put("/{enrollment_id}/cancel", response_model=ApiResponse[EnrollmentResponse])
def cancel_enrollment(enrollment_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COORDINATOR"))):
    enrollment = find_or_404(db, enrollment_id)
    change_status(enrollment, EnrollmentStatus.CANCELLED)
    db.commit()
    db.refresh(enrollment)
    return ApiResponse(success=True, message="Enrollment cancelled successfully", data=to_response(enrollment))


@router.put("/{enrollment_id}/status", response_model=ApiResponse[EnrollmentResponse])
def update_status(enrollment_id: int, request: UpdateEnrollmentStatusRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COORDINATOR"))):
    enrollment = find_or_404(db, enrollment_id)
    change_status(enrollment, request.status)
    db.commit()
    db.refresh(enrollment)
    return ApiResponse(success=True, message="Enrollment status updated successfully", data=to_response(enrollment))
