from typing import List

from fastapi import Depends

from app.dto.request.course_subject import CreateCourseSubjectRequest
from app.dto.response.course_subject import CourseSubjectResponse
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.model import CourseSubject, Teacher, User
from app.repository.course_repository import CourseRepository
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.subject_repository import SubjectRepository
from app.repository.teacher_repository import TeacherRepository


class CourseSubjectService:

    def __init__(
        self,
        course_subject_repository: CourseSubjectRepository = Depends(),
        course_repository: CourseRepository = Depends(),
        subject_repository: SubjectRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
    ):
        self.course_subject_repository = course_subject_repository
        self.course_repository = course_repository
        self.subject_repository = subject_repository
        self.teacher_repository = teacher_repository

    @staticmethod
    def to_response(cs: CourseSubject) -> CourseSubjectResponse:
        return CourseSubjectResponse(
            id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
            subject_id=cs.subject_id, subject_name=cs.subject.name,
            teacher_id=cs.teacher_id, teacher_name=cs.teacher.user.full_name, estado=cs.estado,
        )

    def find_or_404(self, cs_id: int) -> CourseSubject:
        cs = self.course_subject_repository.find_active_by_id(cs_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")
        return cs

    def create_course_subject(self, request: CreateCourseSubjectRequest) -> CourseSubjectResponse:
        course = self.course_repository.find_by_id(request.course_id, include_inactive=True)
        if course is None:
            raise ResourceNotFoundException(f"Course with id {request.course_id} not found")
        if not course.estado:
            raise InvalidRequestException("Cannot assign a subject to an inactive course")

        subject = self.subject_repository.find_by_id(request.subject_id, include_inactive=True)
        if subject is None:
            raise ResourceNotFoundException(f"Subject with id {request.subject_id} not found")
        if not subject.estado:
            raise InvalidRequestException("Cannot assign an inactive subject")

        teacher = self.teacher_repository.find_active_by_id(request.teacher_id)
        if teacher is None:
            raise ResourceNotFoundException(f"Teacher with id {request.teacher_id} not found")

        if self.course_subject_repository.exists_active_by_course_and_subject(course.id, subject.id):
            raise DuplicateResourceException("This subject is already assigned to this course")

        cs = CourseSubject(course_id=course.id, subject_id=subject.id, teacher_id=teacher.id)
        return self.to_response(self.course_subject_repository.save(cs))

    def get_all_course_subjects(self) -> List[CourseSubjectResponse]:
        return [self.to_response(i) for i in self.course_subject_repository.find_all_active()]

    def get_my_subjects(self, current_teacher: Teacher) -> List[CourseSubjectResponse]:
        items = self.course_subject_repository.find_active_by_teacher_id(current_teacher.id)
        return [self.to_response(i) for i in items]

    def get_course_subject_by_id(self, cs_id: int) -> CourseSubjectResponse:
        return self.to_response(self.find_or_404(cs_id))

    def get_course_subjects_by_teacher(self, teacher_id: int, current_user: User) -> List[CourseSubjectResponse]:
        if current_user.role.value == "TEACHER":
            own_teacher = self.teacher_repository.find_active_by_user_id(current_user.id)
            if own_teacher is None or own_teacher.id != teacher_id:
                raise ForbiddenOperationException("You can only view your own assigned subjects")
        items = self.course_subject_repository.find_active_by_teacher_id(teacher_id)
        return [self.to_response(i) for i in items]

    def deactivate_course_subject(self, cs_id: int) -> CourseSubjectResponse:
        cs = self.find_or_404(cs_id)
        cs.estado = False
        self.course_subject_repository.commit()
        self.course_subject_repository.refresh(cs)
        return self.to_response(cs)
