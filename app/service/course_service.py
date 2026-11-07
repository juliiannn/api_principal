from typing import List, Optional

from fastapi import Depends

from app.dto.request.course import AssignDirectorTeacherRequest, CreateCourseRequest
from app.dto.response.course import CourseResponse
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import Course, Teacher, User
from app.repository.course_repository import CourseRepository
from app.repository.teacher_repository import TeacherRepository


class CourseService:

    def __init__(
        self,
        course_repository: CourseRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
    ):
        self.course_repository = course_repository
        self.teacher_repository = teacher_repository

    @staticmethod
    def to_response(c: Course) -> CourseResponse:
        return CourseResponse(
            id=c.id, name=c.name, grade=c.grade, classroom=c.classroom, school_year=c.school_year,
            director_teacher_id=c.director_teacher_id,
            director_teacher_name=c.director_teacher.user.full_name if c.director_teacher else None,
            estado=c.estado,
        )

    def find_or_404(self, course_id: int, include_inactive: bool = False) -> Course:
        c = self.course_repository.find_by_id(course_id, include_inactive)
        if c is None:
            raise ResourceNotFoundException(f"Course with id {course_id} not found")
        return c

    def _check_duplicate(self, name: str, classroom: str, school_year: int, exclude_id: Optional[int] = None) -> None:
        if self.course_repository.exists_duplicate(name, classroom, school_year, exclude_id):
            raise DuplicateResourceException("Course already exists for that school year")

    def _find_teacher_or_404(self, teacher_id: int) -> Teacher:
        teacher = self.teacher_repository.find_active_by_id(teacher_id)
        if teacher is None:
            raise ResourceNotFoundException(f"Teacher with id {teacher_id} not found")
        return teacher

    def create_course(self, request: CreateCourseRequest) -> CourseResponse:
        name, classroom = request.name.strip(), request.classroom.strip()
        self._check_duplicate(name, classroom, request.school_year)

        director_teacher = None
        if request.director_teacher_id is not None:
            director_teacher = self._find_teacher_or_404(request.director_teacher_id)

        course = Course(
            name=name, grade=request.grade.strip(), classroom=classroom, school_year=request.school_year,
            director_teacher_id=director_teacher.id if director_teacher else None,
        )
        return self.to_response(self.course_repository.save(course))

    def update_course(self, course_id: int, request: CreateCourseRequest) -> CourseResponse:
        course = self.find_or_404(course_id)
        name, classroom = request.name.strip(), request.classroom.strip()
        self._check_duplicate(name, classroom, request.school_year, exclude_id=course_id)

        director_teacher = None
        if request.director_teacher_id is not None:
            director_teacher = self._find_teacher_or_404(request.director_teacher_id)

        course.name, course.grade, course.classroom = name, request.grade.strip(), classroom
        course.school_year = request.school_year
        course.director_teacher_id = director_teacher.id if director_teacher else None
        self.course_repository.commit()
        self.course_repository.refresh(course)
        return self.to_response(course)

    def assign_director_teacher(self, course_id: int, request: AssignDirectorTeacherRequest) -> CourseResponse:
        course = self.find_or_404(course_id)
        teacher = self._find_teacher_or_404(request.teacher_id)
        course.director_teacher_id = teacher.id
        self.course_repository.commit()
        self.course_repository.refresh(course)
        return self.to_response(course)

    def get_all_courses(self, include_inactive: bool, current_user: User) -> List[CourseResponse]:
        # Solo el ADMIN puede ver los cursos desactivados (para poder reactivarlos)
        show_inactive = include_inactive and current_user.role_ref.nombre == "ADMIN"
        return [self.to_response(c) for c in self.course_repository.find_all(show_inactive)]

    def get_course_by_id(self, course_id: int) -> CourseResponse:
        return self.to_response(self.find_or_404(course_id))

    def deactivate_course(self, course_id: int) -> CourseResponse:
        course = self.find_or_404(course_id)
        course.estado = False
        self.course_repository.commit()
        self.course_repository.refresh(course)
        return self.to_response(course)

    def activate_course(self, course_id: int) -> CourseResponse:
        course = self.find_or_404(course_id, include_inactive=True)
        course.estado = True
        self.course_repository.commit()
        self.course_repository.refresh(course)
        return self.to_response(course)
