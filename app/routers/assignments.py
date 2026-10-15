from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, get_current_teacher, require_role
from app.exceptions import ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.models import Assignment, CourseSubject, Enrollment, EnrollmentStatus, Student, Teacher, User
from app.schemas import ApiResponse, AssignmentResponse, CreateAssignmentRequest
from app.utils import ensure_teacher_teaches_course_subject

router = APIRouter(prefix="/assignments", tags=["Assignments"])


def to_response(a: Assignment) -> AssignmentResponse:
    cs = a.course_subject
    return AssignmentResponse(
        id=a.id, course_subject_id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
        subject_id=cs.subject_id, subject_name=cs.subject.name, teacher_name=cs.teacher.user.full_name,
        title=a.title, description=a.description, due_date=a.due_date, estado=a.estado, creado=a.creado,
    )


@router.post("", response_model=ApiResponse[AssignmentResponse], status_code=201)
def create_assignment(request: CreateAssignmentRequest, db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    cs = db.query(CourseSubject).filter(CourseSubject.id == request.course_subject_id).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
    if cs.teacher_id != current_teacher.id:
        raise ForbiddenOperationException("You can only publish assignments for subjects assigned to you")
    if not cs.estado:
        raise InvalidRequestException("Cannot publish an assignment for an inactive course-subject assignment")

    assignment = Assignment(course_subject_id=cs.id, title=request.title.strip(), description=request.description.strip(), due_date=request.due_date)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return ApiResponse(success=True, message="Assignment published successfully", data=to_response(assignment))


@router.get("/me", response_model=ApiResponse[List[AssignmentResponse]])
def get_my_assignments(db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    enrollment = db.query(Enrollment).filter(Enrollment.student_id == current_student.id, Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)).first()
    if enrollment is None:
        raise ResourceNotFoundException("You are not actively enrolled in any course")
    items = db.query(Assignment).join(CourseSubject).filter(
        CourseSubject.course_id == enrollment.course_id, Assignment.estado.is_(True), CourseSubject.estado.is_(True)
    ).all()
    return ApiResponse(success=True, message="Assignments retrieved successfully", data=[to_response(a) for a in items])


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[AssignmentResponse]])
def get_assignments_by_course_subject(cs_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    if current_user.role_ref.nombre == "TEACHER":
        ensure_teacher_teaches_course_subject(db, current_user, cs_id)
    items = db.query(Assignment).filter(Assignment.course_subject_id == cs_id, Assignment.estado.is_(True)).all()
    return ApiResponse(success=True, message="Assignments retrieved successfully", data=[to_response(a) for a in items])
