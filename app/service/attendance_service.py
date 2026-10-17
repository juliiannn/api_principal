from datetime import date as date_type
from typing import List

from fastapi import Depends

from app.dto.request.attendance import CreateAttendanceRequest, CreateBulkAttendanceRequest
from app.dto.response.attendance import AttendanceResponse
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.model import Attendance, CourseSubject, Student, Teacher, User
from app.repository.attendance_repository import AttendanceRepository
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.student_repository import StudentRepository
from app.service.current_user_service import CurrentUserService


class AttendanceService:

    def __init__(
        self,
        attendance_repository: AttendanceRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        enrollment_repository: EnrollmentRepository = Depends(),
        current_user_service: CurrentUserService = Depends(),
    ):
        self.attendance_repository = attendance_repository
        self.student_repository = student_repository
        self.course_subject_repository = course_subject_repository
        self.enrollment_repository = enrollment_repository
        self.current_user_service = current_user_service

    @staticmethod
    def to_response(a: Attendance) -> AttendanceResponse:
        return AttendanceResponse(
            id=a.id, student_id=a.student_id, student_name=a.student.user.full_name,
            course_subject_id=a.course_subject_id, subject_name=a.course_subject.subject.name,
            course_name=a.course_subject.course.name, date=a.date, status=a.status,
        )

    @staticmethod
    def _check_ownership(cs: CourseSubject, current_teacher: Teacher) -> None:
        if cs.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only register attendance for subjects assigned to you")

    def _validate_assignable(self, student: Student, cs: CourseSubject, the_date: date_type) -> None:
        if not cs.estado:
            raise InvalidRequestException("Cannot register attendance for an inactive course-subject assignment")
        if not self.enrollment_repository.exists_active_in_course(student.id, cs.course_id):
            raise InvalidRequestException("Student is not actively enrolled in this course")
        if self.attendance_repository.exists_by_student_course_subject_date(student.id, cs.id, the_date):
            raise DuplicateResourceException("Attendance already registered for this student, subject and date")

    def _find_course_subject_or_404(self, cs_id: int) -> CourseSubject:
        cs = self.course_subject_repository.find_by_id(cs_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")
        return cs

    def create_attendance(self, request: CreateAttendanceRequest, current_teacher: Teacher) -> AttendanceResponse:
        student = self.student_repository.find_active_by_id(request.student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {request.student_id} not found")
        cs = self._find_course_subject_or_404(request.course_subject_id)
        self._check_ownership(cs, current_teacher)
        self._validate_assignable(student, cs, request.date)

        attendance = Attendance(
            student_id=student.id, course_subject_id=cs.id, date=request.date, status=request.status
        )
        return self.to_response(self.attendance_repository.save(attendance))

    def create_bulk_attendance(
        self, request: CreateBulkAttendanceRequest, current_teacher: Teacher
    ) -> List[AttendanceResponse]:
        cs = self._find_course_subject_or_404(request.course_subject_id)
        self._check_ownership(cs, current_teacher)

        results = []
        for record in request.records:
            student = self.student_repository.find_active_by_id(record.student_id)
            if student is None:
                raise ResourceNotFoundException(f"Student with id {record.student_id} not found")
            self._validate_assignable(student, cs, request.date)
            attendance = Attendance(
                student_id=student.id, course_subject_id=cs.id, date=request.date, status=record.status
            )
            self.attendance_repository.add(attendance)
            self.attendance_repository.flush()
            results.append(attendance)

        self.attendance_repository.commit()
        for a in results:
            self.attendance_repository.refresh(a)
        return [self.to_response(a) for a in results]

    def get_my_attendance(self, current_user: User) -> List[AttendanceResponse]:
        student = self.student_repository.find_active_by_user_id(current_user.id)
        if student is None:
            raise ResourceNotFoundException("No student profile found for the authenticated user")
        return [self.to_response(a) for a in self.attendance_repository.find_active_by_student(student.id)]

    def get_attendance_by_student(self, student_id: int, current_user: User) -> List[AttendanceResponse]:
        if current_user.role.value == "STUDENT":
            own_student = self.student_repository.find_active_by_user_id(current_user.id)
            if own_student is None or own_student.id != student_id:
                raise ForbiddenOperationException("You can only view your own attendance")
        elif current_user.role.value == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_student(current_user, student_id)
        return [self.to_response(a) for a in self.attendance_repository.find_active_by_student(student_id)]

    def get_attendance_by_course_subject_and_date(
        self, cs_id: int, the_date: date_type, current_user: User
    ) -> List[AttendanceResponse]:
        if current_user.role_ref.nombre == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(current_user, cs_id)
        items = self.attendance_repository.find_active_by_course_subject_and_date(cs_id, the_date)
        return [self.to_response(a) for a in items]
