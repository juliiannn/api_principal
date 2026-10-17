from typing import List

from fastapi import Depends

from app.dto.request.grade import CreateGradeRequest, UpdateGradeRequest
from app.dto.response.grade import GradeResponse
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.model import Grade, Teacher, User
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.grade_repository import GradeRepository
from app.repository.student_repository import StudentRepository
from app.service.current_user_service import CurrentUserService


class GradeService:

    def __init__(
        self,
        grade_repository: GradeRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        enrollment_repository: EnrollmentRepository = Depends(),
        current_user_service: CurrentUserService = Depends(),
    ):
        self.grade_repository = grade_repository
        self.student_repository = student_repository
        self.course_subject_repository = course_subject_repository
        self.enrollment_repository = enrollment_repository
        self.current_user_service = current_user_service

    @staticmethod
    def to_response(g: Grade) -> GradeResponse:
        return GradeResponse(
            id=g.id, student_id=g.student_id, student_name=g.student.user.full_name,
            course_subject_id=g.course_subject_id, subject_name=g.course_subject.subject.name,
            course_name=g.course_subject.course.name, teacher_name=g.course_subject.teacher.user.full_name,
            period=g.period, value=g.value,
        )

    def find_or_404(self, grade_id: int) -> Grade:
        g = self.grade_repository.find_active_by_id(grade_id)
        if g is None:
            raise ResourceNotFoundException(f"Grade with id {grade_id} not found")
        return g

    def _own_student(self, user: User):
        return self.student_repository.find_active_by_user_id(user.id)

    def create_grade(self, request: CreateGradeRequest, current_teacher: Teacher) -> GradeResponse:
        student = self.student_repository.find_active_by_id(request.student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

        cs = self.course_subject_repository.find_by_id(request.course_subject_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
        if cs.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only register grades for subjects assigned to you")
        if not cs.estado:
            raise InvalidRequestException("Cannot register a grade for an inactive course-subject assignment")

        if not self.enrollment_repository.exists_active_in_course(student.id, cs.course_id):
            raise InvalidRequestException("Student is not actively enrolled in this course")

        if self.grade_repository.exists_by_student_course_subject_period(student.id, cs.id, request.period):
            raise DuplicateResourceException("A grade already exists for this student, subject and period")

        grade = Grade(student_id=student.id, course_subject_id=cs.id, period=request.period, value=request.value)
        return self.to_response(self.grade_repository.save(grade))

    def update_grade(self, grade_id: int, request: UpdateGradeRequest, current_teacher: Teacher) -> GradeResponse:
        grade = self.find_or_404(grade_id)
        if grade.course_subject.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only edit grades for subjects assigned to you")
        grade.value = request.value
        self.grade_repository.commit()
        self.grade_repository.refresh(grade)
        return self.to_response(grade)

    def get_my_grades(self, current_user: User) -> List[GradeResponse]:
        student = self._own_student(current_user)
        if student is None:
            raise ResourceNotFoundException("No student profile found for the authenticated user")
        return [self.to_response(g) for g in self.grade_repository.find_active_by_student(student.id)]

    def get_grade_by_id(self, grade_id: int, current_user: User) -> GradeResponse:
        grade = self.find_or_404(grade_id)
        role = current_user.role_ref.nombre
        if role == "STUDENT":
            own_student = self._own_student(current_user)
            if own_student is None or own_student.id != grade.student_id:
                raise ForbiddenOperationException("You can only view your own grades")
        elif role == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(current_user, grade.course_subject_id)
        return self.to_response(grade)

    def get_grades_by_student(self, student_id: int, current_user: User) -> List[GradeResponse]:
        if current_user.role.value == "STUDENT":
            own_student = self._own_student(current_user)
            if own_student is None or own_student.id != student_id:
                raise ForbiddenOperationException("You can only view your own grades")
        elif current_user.role.value == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_student(current_user, student_id)
        return [self.to_response(g) for g in self.grade_repository.find_active_by_student(student_id)]

    def get_grades_by_course_subject(self, cs_id: int, current_user: User) -> List[GradeResponse]:
        if current_user.role_ref.nombre == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(current_user, cs_id)
        return [self.to_response(g) for g in self.grade_repository.find_active_by_course_subject(cs_id)]
