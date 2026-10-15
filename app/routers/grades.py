from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_teacher, require_role
from app.exceptions import DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.models import CourseSubject, Enrollment, EnrollmentStatus, Grade, Student, Teacher, User
from app.schemas import ApiResponse, CreateGradeRequest, GradeResponse, UpdateGradeRequest
from app.utils import ensure_teacher_teaches_course_subject, ensure_teacher_teaches_student

router = APIRouter(prefix="/grades", tags=["Grades"])


def to_response(g: Grade) -> GradeResponse:
    return GradeResponse(
        id=g.id, student_id=g.student_id, student_name=g.student.user.full_name,
        course_subject_id=g.course_subject_id, subject_name=g.course_subject.subject.name,
        course_name=g.course_subject.course.name, teacher_name=g.course_subject.teacher.user.full_name,
        period=g.period, value=g.value,
    )


def find_or_404(db: Session, grade_id: int) -> Grade:
    g = db.query(Grade).filter(Grade.id == grade_id, Grade.estado.is_(True)).first()
    if g is None:
        raise ResourceNotFoundException(f"Grade with id {grade_id} not found")
    return g


@router.post("", response_model=ApiResponse[GradeResponse], status_code=201)
def create_grade(request: CreateGradeRequest, db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    student = db.query(Student).filter(Student.id == request.student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

    cs = db.query(CourseSubject).filter(CourseSubject.id == request.course_subject_id).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")

    if cs.teacher_id != current_teacher.id:
        raise ForbiddenOperationException("You can only register grades for subjects assigned to you")
    if not cs.estado:
        raise InvalidRequestException("Cannot register a grade for an inactive course-subject assignment")

    enrolled = db.query(Enrollment).filter(
        Enrollment.student_id == student.id, Enrollment.course_id == cs.course_id, Enrollment.status == EnrollmentStatus.ACTIVE,
        Enrollment.estado.is_(True)
    ).first()
    if not enrolled:
        raise InvalidRequestException("Student is not actively enrolled in this course")

    duplicate = db.query(Grade).filter(
        Grade.student_id == student.id, Grade.course_subject_id == cs.id, Grade.period == request.period
    ).first()
    if duplicate:
        raise DuplicateResourceException("A grade already exists for this student, subject and period")

    grade = Grade(student_id=student.id, course_subject_id=cs.id, period=request.period, value=request.value)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return ApiResponse(success=True, message="Grade registered successfully", data=to_response(grade))


@router.put("/{grade_id}", response_model=ApiResponse[GradeResponse])
def update_grade(grade_id: int, request: UpdateGradeRequest, db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    grade = find_or_404(db, grade_id)
    if grade.course_subject.teacher_id != current_teacher.id:
        raise ForbiddenOperationException("You can only edit grades for subjects assigned to you")
    grade.value = request.value
    db.commit()
    db.refresh(grade)
    return ApiResponse(success=True, message="Grade updated successfully", data=to_response(grade))


@router.get("/me", response_model=ApiResponse[List[GradeResponse]])
def get_my_grades(db: Session = Depends(get_db), current_user: User = Depends(require_role("STUDENT"))):
    student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException("No student profile found for the authenticated user")
    grades = db.query(Grade).filter(Grade.student_id == student.id, Grade.estado.is_(True)).all()
    return ApiResponse(success=True, message="Grades retrieved successfully", data=[to_response(g) for g in grades])


@router.get("/{grade_id}", response_model=ApiResponse[GradeResponse])
def get_grade_by_id(
    grade_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    grade = find_or_404(db, grade_id)
    role = current_user.role_ref.nombre
    if role == "STUDENT":
        own_student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
        if own_student is None or own_student.id != grade.student_id:
            raise ForbiddenOperationException("You can only view your own grades")
    elif role == "TEACHER":
        ensure_teacher_teaches_course_subject(db, current_user, grade.course_subject_id)
    return ApiResponse(success=True, message="Grade retrieved successfully", data=to_response(grade))


@router.get("/student/{student_id}", response_model=ApiResponse[List[GradeResponse]])
def get_grades_by_student(
    student_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    if current_user.role.value == "STUDENT":
        own_student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
        if own_student is None or own_student.id != student_id:
            raise ForbiddenOperationException("You can only view your own grades")
    elif current_user.role.value == "TEACHER":
        ensure_teacher_teaches_student(db, current_user, student_id)

    grades = db.query(Grade).filter(Grade.student_id == student_id, Grade.estado.is_(True)).all()
    return ApiResponse(success=True, message="Grades retrieved successfully", data=[to_response(g) for g in grades])


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[GradeResponse]])
def get_grades_by_course_subject(cs_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    if current_user.role_ref.nombre == "TEACHER":
        ensure_teacher_teaches_course_subject(db, current_user, cs_id)
    grades = db.query(Grade).filter(Grade.course_subject_id == cs_id, Grade.estado.is_(True)).all()
    return ApiResponse(success=True, message="Grades retrieved successfully", data=[to_response(g) for g in grades])
