from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Course, Teacher, User
from app.schemas import ApiResponse, AssignDirectorTeacherRequest, CreateCourseRequest, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


def to_response(c: Course) -> CourseResponse:
    return CourseResponse(
        id=c.id, name=c.name, grade=c.grade, classroom=c.classroom, school_year=c.school_year,
        director_teacher_id=c.director_teacher_id,
        director_teacher_name=c.director_teacher.user.full_name if c.director_teacher else None,
        estado=c.estado,
    )


def find_or_404(db: Session, course_id: int, include_inactive: bool = False) -> Course:
    q = db.query(Course).filter(Course.id == course_id)
    if not include_inactive:
        q = q.filter(Course.estado.is_(True))
    c = q.first()
    if c is None:
        raise ResourceNotFoundException(f"Course with id {course_id} not found")
    return c


def check_duplicate(db: Session, name: str, classroom: str, school_year: int, exclude_id: int = None):
    q = db.query(Course).filter(Course.name == name, Course.classroom.ilike(classroom), Course.school_year == school_year, Course.estado.is_(True))
    if exclude_id is not None:
        q = q.filter(Course.id != exclude_id)
    if q.first():
        raise DuplicateResourceException("Course already exists for that school year")


@router.post("", response_model=ApiResponse[CourseResponse], status_code=201)
def create_course(request: CreateCourseRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    name, classroom = request.name.strip(), request.classroom.strip()
    check_duplicate(db, name, classroom, request.school_year)

    director_teacher = None
    if request.director_teacher_id is not None:
        director_teacher = db.query(Teacher).filter(Teacher.id == request.director_teacher_id, Teacher.estado.is_(True)).first()
        if director_teacher is None:
            raise ResourceNotFoundException(f"Teacher with id {request.director_teacher_id} not found")

    course = Course(
        name=name, grade=request.grade.strip(), classroom=classroom, school_year=request.school_year,
        director_teacher_id=director_teacher.id if director_teacher else None,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return ApiResponse(success=True, message="Course created successfully", data=to_response(course))


@router.put("/{course_id}", response_model=ApiResponse[CourseResponse])
def update_course(course_id: int, request: CreateCourseRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    course = find_or_404(db, course_id)
    name, classroom = request.name.strip(), request.classroom.strip()
    check_duplicate(db, name, classroom, request.school_year, exclude_id=course_id)

    director_teacher = None
    if request.director_teacher_id is not None:
        director_teacher = db.query(Teacher).filter(Teacher.id == request.director_teacher_id, Teacher.estado.is_(True)).first()
        if director_teacher is None:
            raise ResourceNotFoundException(f"Teacher with id {request.director_teacher_id} not found")

    course.name, course.grade, course.classroom = name, request.grade.strip(), classroom
    course.school_year = request.school_year
    course.director_teacher_id = director_teacher.id if director_teacher else None
    db.commit()
    db.refresh(course)
    return ApiResponse(success=True, message="Course updated successfully", data=to_response(course))


@router.put("/{course_id}/director-teacher", response_model=ApiResponse[CourseResponse])
def assign_director_teacher(course_id: int, request: AssignDirectorTeacherRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    course = find_or_404(db, course_id)
    teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id, Teacher.estado.is_(True)).first()
    if teacher is None:
        raise ResourceNotFoundException(f"Teacher with id {request.teacher_id} not found")
    course.director_teacher_id = teacher.id
    db.commit()
    db.refresh(course)
    return ApiResponse(success=True, message="Director teacher assigned successfully", data=to_response(course))


@router.get("", response_model=ApiResponse[List[CourseResponse]])
def get_all_courses(
    include_inactive: bool = False, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    q = db.query(Course)
    # Solo el ADMIN puede ver los cursos desactivados (para poder reactivarlos)
    if not (include_inactive and current_user.role_ref.nombre == "ADMIN"):
        q = q.filter(Course.estado.is_(True))
    courses = q.all()
    return ApiResponse(success=True, message="Courses retrieved successfully", data=[to_response(c) for c in courses])


@router.get("/{course_id}", response_model=ApiResponse[CourseResponse])
def get_course_by_id(course_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    return ApiResponse(success=True, message="Course retrieved successfully", data=to_response(find_or_404(db, course_id)))


@router.put("/{course_id}/deactivate", response_model=ApiResponse[CourseResponse])
def deactivate_course(course_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    course = find_or_404(db, course_id)
    course.estado = False
    db.commit()
    db.refresh(course)
    return ApiResponse(success=True, message="Course deactivated successfully", data=to_response(course))


@router.put("/{course_id}/activate", response_model=ApiResponse[CourseResponse])
def activate_course(course_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    course = find_or_404(db, course_id, include_inactive=True)
    course.estado = True
    db.commit()
    db.refresh(course)
    return ApiResponse(success=True, message="Course activated successfully", data=to_response(course))
