from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_teacher, require_role
from app.exceptions import DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.models import Course, CourseSubject, Subject, Teacher, User
from app.schemas import ApiResponse, CreateCourseSubjectRequest, CourseSubjectResponse

router = APIRouter(prefix="/course-subjects", tags=["CourseSubjects"])


def to_response(cs: CourseSubject) -> CourseSubjectResponse:
    return CourseSubjectResponse(
        id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
        subject_id=cs.subject_id, subject_name=cs.subject.name,
        teacher_id=cs.teacher_id, teacher_name=cs.teacher.user.full_name, estado=cs.estado,
    )


def find_or_404(db: Session, cs_id: int) -> CourseSubject:
    cs = db.query(CourseSubject).filter(CourseSubject.id == cs_id, CourseSubject.estado.is_(True)).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")
    return cs


@router.post("", response_model=ApiResponse[CourseSubjectResponse], status_code=201)
def create_course_subject(request: CreateCourseSubjectRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    course = db.query(Course).filter(Course.id == request.course_id).first()
    if course is None:
        raise ResourceNotFoundException(f"Course with id {request.course_id} not found")
    if not course.estado:
        raise InvalidRequestException("Cannot assign a subject to an inactive course")

    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if subject is None:
        raise ResourceNotFoundException(f"Subject with id {request.subject_id} not found")
    if not subject.estado:
        raise InvalidRequestException("Cannot assign an inactive subject")

    teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id, Teacher.estado.is_(True)).first()
    if teacher is None:
        raise ResourceNotFoundException(f"Teacher with id {request.teacher_id} not found")

    existing = db.query(CourseSubject).filter(
        CourseSubject.course_id == course.id, CourseSubject.subject_id == subject.id, CourseSubject.estado.is_(True)
    ).first()
    if existing:
        raise DuplicateResourceException("This subject is already assigned to this course")

    cs = CourseSubject(course_id=course.id, subject_id=subject.id, teacher_id=teacher.id)
    db.add(cs)
    db.commit()
    db.refresh(cs)
    return ApiResponse(success=True, message="Subject assigned to course successfully", data=to_response(cs))


@router.get("", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_all_course_subjects(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    items = db.query(CourseSubject).filter(CourseSubject.estado.is_(True)).all()
    return ApiResponse(success=True, message="Course-subject assignments retrieved successfully", data=[to_response(i) for i in items])


@router.get("/me", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_my_subjects(db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    items = db.query(CourseSubject).filter(CourseSubject.teacher_id == current_teacher.id, CourseSubject.estado.is_(True)).all()
    return ApiResponse(success=True, message="Your subjects retrieved successfully", data=[to_response(i) for i in items])


@router.get("/{cs_id}", response_model=ApiResponse[CourseSubjectResponse])
def get_course_subject_by_id(cs_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    return ApiResponse(success=True, message="Course-subject assignment retrieved successfully", data=to_response(find_or_404(db, cs_id)))


@router.get("/teacher/{teacher_id}", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_course_subjects_by_teacher(
    teacher_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    if current_user.role.value == "TEACHER":
        own_teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id, Teacher.estado.is_(True)).first()
        if own_teacher is None or own_teacher.id != teacher_id:
            raise ForbiddenOperationException("You can only view your own assigned subjects")

    items = db.query(CourseSubject).filter(CourseSubject.teacher_id == teacher_id, CourseSubject.estado.is_(True)).all()
    return ApiResponse(success=True, message="Teacher's subjects retrieved successfully", data=[to_response(i) for i in items])


@router.put("/{cs_id}/deactivate", response_model=ApiResponse[CourseSubjectResponse])
def deactivate_course_subject(cs_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    cs = find_or_404(db, cs_id)
    cs.estado = False
    db.commit()
    db.refresh(cs)
    return ApiResponse(success=True, message="Assignment deactivated successfully", data=to_response(cs))
