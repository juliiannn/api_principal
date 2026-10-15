from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, get_current_teacher, require_role
from app.exceptions import InvalidRequestException, ResourceNotFoundException
from app.models import CourseSubject, Enrollment, EnrollmentStatus, Schedule, Student, Teacher, User
from app.schemas import ApiResponse, CreateScheduleRequest, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["Schedules"])


def to_response(s: Schedule) -> ScheduleResponse:
    cs = s.course_subject
    return ScheduleResponse(
        id=s.id, course_subject_id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
        subject_id=cs.subject_id, subject_name=cs.subject.name, teacher_id=cs.teacher_id,
        teacher_name=cs.teacher.user.full_name, day_of_week=s.day_of_week,
        start_time=s.start_time, end_time=s.end_time,
    )


def overlaps(existing_start, existing_end, new_start, new_end) -> bool:
    return new_start < existing_end and existing_start < new_end


@router.post("", response_model=ApiResponse[ScheduleResponse], status_code=201)
def create_schedule(request: CreateScheduleRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    if request.start_time >= request.end_time:
        raise InvalidRequestException("Start time must be before end time")

    cs = db.query(CourseSubject).filter(CourseSubject.id == request.course_subject_id).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
    if not cs.estado:
        raise InvalidRequestException("Cannot schedule an inactive course-subject assignment")

    course_schedules = db.query(Schedule).join(CourseSubject).filter(
        CourseSubject.course_id == cs.course_id, Schedule.day_of_week == request.day_of_week,
        Schedule.estado.is_(True)
    ).all()
    for existing in course_schedules:
        if overlaps(existing.start_time, existing.end_time, request.start_time, request.end_time):
            raise InvalidRequestException(f"This course already has a class scheduled at that time on {request.day_of_week.value}")

    teacher_schedules = db.query(Schedule).join(CourseSubject).filter(
        CourseSubject.teacher_id == cs.teacher_id, Schedule.day_of_week == request.day_of_week,
        Schedule.estado.is_(True)
    ).all()
    for existing in teacher_schedules:
        if overlaps(existing.start_time, existing.end_time, request.start_time, request.end_time):
            raise InvalidRequestException(f"This teacher already has another class scheduled at that time on {request.day_of_week.value}")

    schedule = Schedule(course_subject_id=cs.id, day_of_week=request.day_of_week, start_time=request.start_time, end_time=request.end_time)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ApiResponse(success=True, message="Schedule created successfully", data=to_response(schedule))


@router.get("/me", response_model=ApiResponse[List[ScheduleResponse]])
def get_my_schedule(db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    enrollment = db.query(Enrollment).filter(Enrollment.student_id == current_student.id, Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)).first()
    if enrollment is None:
        raise ResourceNotFoundException("You are not actively enrolled in any course")
    items = db.query(Schedule).join(CourseSubject).filter(
        CourseSubject.course_id == enrollment.course_id, Schedule.estado.is_(True)
    ).all()
    return ApiResponse(success=True, message="Schedule retrieved successfully", data=[to_response(s) for s in items])


@router.get("/teacher/me", response_model=ApiResponse[List[ScheduleResponse]])
def get_my_teaching_schedule(db: Session = Depends(get_db), current_teacher: Teacher = Depends(get_current_teacher)):
    items = db.query(Schedule).join(CourseSubject).filter(
        CourseSubject.teacher_id == current_teacher.id, Schedule.estado.is_(True)
    ).all()
    return ApiResponse(success=True, message="Teaching schedule retrieved successfully", data=[to_response(s) for s in items])


@router.get("/course/{course_id}", response_model=ApiResponse[List[ScheduleResponse]])
def get_schedules_by_course(course_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    items = db.query(Schedule).join(CourseSubject).filter(
        CourseSubject.course_id == course_id, Schedule.estado.is_(True)
    ).all()
    return ApiResponse(success=True, message="Schedule retrieved successfully", data=[to_response(s) for s in items])


@router.delete("/{schedule_id}", response_model=ApiResponse[None])
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.estado.is_(True)).first()
    if schedule is None:
        raise ResourceNotFoundException(f"Schedule with id {schedule_id} not found")
    schedule.estado = False  # borrado lógico: el registro no se elimina de la tabla
    db.commit()
    return ApiResponse(success=True, message="Schedule deleted successfully", data=None)
