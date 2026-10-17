from typing import List

from fastapi import Depends

from app.dto.request.schedule import CreateScheduleRequest
from app.dto.response.schedule import ScheduleResponse
from app.exception import InvalidRequestException, ResourceNotFoundException
from app.model import Schedule, Student, Teacher
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.schedule_repository import ScheduleRepository


def overlaps(existing_start, existing_end, new_start, new_end) -> bool:
    return new_start < existing_end and existing_start < new_end


class ScheduleService:

    def __init__(
        self,
        schedule_repository: ScheduleRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        enrollment_repository: EnrollmentRepository = Depends(),
    ):
        self.schedule_repository = schedule_repository
        self.course_subject_repository = course_subject_repository
        self.enrollment_repository = enrollment_repository

    @staticmethod
    def to_response(s: Schedule) -> ScheduleResponse:
        cs = s.course_subject
        return ScheduleResponse(
            id=s.id, course_subject_id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
            subject_id=cs.subject_id, subject_name=cs.subject.name, teacher_id=cs.teacher_id,
            teacher_name=cs.teacher.user.full_name, day_of_week=s.day_of_week,
            start_time=s.start_time, end_time=s.end_time,
        )

    def create_schedule(self, request: CreateScheduleRequest) -> ScheduleResponse:
        if request.start_time >= request.end_time:
            raise InvalidRequestException("Start time must be before end time")

        cs = self.course_subject_repository.find_by_id(request.course_subject_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
        if not cs.estado:
            raise InvalidRequestException("Cannot schedule an inactive course-subject assignment")

        for existing in self.schedule_repository.find_active_by_course_and_day(cs.course_id, request.day_of_week):
            if overlaps(existing.start_time, existing.end_time, request.start_time, request.end_time):
                raise InvalidRequestException(
                    f"This course already has a class scheduled at that time on {request.day_of_week.value}"
                )

        for existing in self.schedule_repository.find_active_by_teacher_and_day(cs.teacher_id, request.day_of_week):
            if overlaps(existing.start_time, existing.end_time, request.start_time, request.end_time):
                raise InvalidRequestException(
                    f"This teacher already has another class scheduled at that time on {request.day_of_week.value}"
                )

        schedule = Schedule(
            course_subject_id=cs.id, day_of_week=request.day_of_week,
            start_time=request.start_time, end_time=request.end_time,
        )
        return self.to_response(self.schedule_repository.save(schedule))

    def get_my_schedule(self, current_student: Student) -> List[ScheduleResponse]:
        enrollment = self.enrollment_repository.find_current_by_student(current_student.id)
        if enrollment is None:
            raise ResourceNotFoundException("You are not actively enrolled in any course")
        return [self.to_response(s) for s in self.schedule_repository.find_active_by_course(enrollment.course_id)]

    def get_my_teaching_schedule(self, current_teacher: Teacher) -> List[ScheduleResponse]:
        return [self.to_response(s) for s in self.schedule_repository.find_active_by_teacher(current_teacher.id)]

    def get_schedules_by_course(self, course_id: int) -> List[ScheduleResponse]:
        return [self.to_response(s) for s in self.schedule_repository.find_active_by_course(course_id)]

    def delete_schedule(self, schedule_id: int) -> None:
        schedule = self.schedule_repository.find_active_by_id(schedule_id)
        if schedule is None:
            raise ResourceNotFoundException(f"Schedule with id {schedule_id} not found")
        schedule.estado = False  # borrado lógico: el registro no se elimina de la tabla
        self.schedule_repository.commit()
