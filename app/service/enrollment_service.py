from typing import List

from fastapi import Depends

from app.dto.request.enrollment import (
    CreateEnrollmentRequest, TransferEnrollmentRequest, UpdateEnrollmentStatusRequest,
)
from app.dto.response.enrollment import EnrollmentResponse
from app.dto.response.student import StudentResponse
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException,
    InvalidStatusTransitionException, ResourceNotFoundException,
)
from app.model import Enrollment, EnrollmentStatus, User
from app.repository.course_repository import CourseRepository
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository

VALID_TRANSITIONS = {
    EnrollmentStatus.ACTIVE: {EnrollmentStatus.CANCELLED, EnrollmentStatus.COMPLETED},
    EnrollmentStatus.CANCELLED: set(),
    EnrollmentStatus.COMPLETED: set(),
}


class EnrollmentService:

    def __init__(
        self,
        enrollment_repository: EnrollmentRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        course_repository: CourseRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
    ):
        self.enrollment_repository = enrollment_repository
        self.student_repository = student_repository
        self.course_repository = course_repository
        self.course_subject_repository = course_subject_repository
        self.teacher_repository = teacher_repository

    @staticmethod
    def to_response(e: Enrollment) -> EnrollmentResponse:
        return EnrollmentResponse(
            id=e.id, student_id=e.student_id, student_name=e.student.user.full_name,
            course_id=e.course_id, course_name=e.course.name,
            enrollment_date=e.enrollment_date, status=e.status,
        )

    def find_or_404(self, enrollment_id: int) -> Enrollment:
        e = self.enrollment_repository.find_active_by_id(enrollment_id)
        if e is None:
            raise ResourceNotFoundException(f"Enrollment with id {enrollment_id} not found")
        return e

    @staticmethod
    def _change_status(enrollment: Enrollment, new_status: EnrollmentStatus) -> None:
        if enrollment.status == new_status:
            return
        if new_status not in VALID_TRANSITIONS.get(enrollment.status, set()):
            raise InvalidStatusTransitionException(
                f"Cannot change enrollment status from {enrollment.status.value} to {new_status.value}"
            )
        enrollment.status = new_status

    def create_enrollment(self, request: CreateEnrollmentRequest) -> EnrollmentResponse:
        student = self.student_repository.find_active_by_id(request.student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

        course = self.course_repository.find_by_id(request.course_id, include_inactive=True)
        if course is None:
            raise ResourceNotFoundException(f"Course with id {request.course_id} not found")
        if not course.estado:
            raise InvalidRequestException("Cannot enroll a student in an inactive course")

        if self.enrollment_repository.exists_active_in_course(student.id, course.id):
            raise DuplicateResourceException("Student already enrolled in this course")

        enrollment = Enrollment(student_id=student.id, course_id=course.id)
        return self.to_response(self.enrollment_repository.save(enrollment))

    def transfer_student(self, request: TransferEnrollmentRequest) -> EnrollmentResponse:
        student = self.student_repository.find_active_by_id(request.student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {request.student_id} not found")

        current = self.enrollment_repository.find_current_by_student(student.id)
        if current is None:
            raise ResourceNotFoundException("Student has no active enrollment to transfer from")

        new_course = self.course_repository.find_by_id(request.new_course_id, include_inactive=True)
        if new_course is None:
            raise ResourceNotFoundException(f"Course with id {request.new_course_id} not found")
        if not new_course.estado:
            raise InvalidRequestException("Cannot enroll a student in an inactive course")
        if current.course_id == new_course.id:
            raise InvalidRequestException("Student is already enrolled in that course")

        if self.enrollment_repository.exists_active_in_course(student.id, new_course.id):
            raise DuplicateResourceException("Student already enrolled in the target course")

        self._change_status(current, EnrollmentStatus.CANCELLED)
        self.enrollment_repository.add(current)
        new_enrollment = Enrollment(student_id=student.id, course_id=new_course.id)
        return self.to_response(self.enrollment_repository.save(new_enrollment))

    def get_all_enrollments(self) -> List[EnrollmentResponse]:
        return [self.to_response(i) for i in self.enrollment_repository.find_all_active()]

    def get_enrollment_by_id(self, enrollment_id: int) -> EnrollmentResponse:
        return self.to_response(self.find_or_404(enrollment_id))

    def get_students_by_course(self, course_id: int, current_user: User) -> List[StudentResponse]:
        course = self.course_repository.find_by_id(course_id, include_inactive=True)
        if course is None:
            raise ResourceNotFoundException(f"Course with id {course_id} not found")

        if current_user.role.value == "TEACHER":
            teacher = self.teacher_repository.find_active_by_user_id(current_user.id)
            teaches_here = teacher is not None and self.course_subject_repository.exists_active_by_course_and_teacher(
                course_id, teacher.id
            )
            if not teaches_here:
                raise ForbiddenOperationException("You can only view students from courses where you teach")

        enrollments = self.enrollment_repository.find_active_by_course(course_id)
        return [
            StudentResponse(
                id=e.student.id, user_id=e.student.user.id, document=e.student.user.document,
                full_name=e.student.user.full_name, email=e.student.user.email, phone=e.student.user.phone,
                birth_date=e.student.user.birth_date, enabled=e.student.user.enabled,
                guardian_name=e.student.guardian_name, guardian_phone=e.student.guardian_phone,
                guardian_email=e.student.guardian_email,
            )
            for e in enrollments
        ]

    def cancel_enrollment(self, enrollment_id: int) -> EnrollmentResponse:
        enrollment = self.find_or_404(enrollment_id)
        self._change_status(enrollment, EnrollmentStatus.CANCELLED)
        self.enrollment_repository.commit()
        self.enrollment_repository.refresh(enrollment)
        return self.to_response(enrollment)

    def update_status(self, enrollment_id: int, request: UpdateEnrollmentStatusRequest) -> EnrollmentResponse:
        enrollment = self.find_or_404(enrollment_id)
        self._change_status(enrollment, request.status)
        self.enrollment_repository.commit()
        self.enrollment_repository.refresh(enrollment)
        return self.to_response(enrollment)
