from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_student, get_current_teacher, require_role
from app.dto.request.schedule import CreateScheduleRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.schedule import ScheduleResponse
from app.model import Student, Teacher, User
from app.service.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("", response_model=ApiResponse[ScheduleResponse], status_code=201)
def create_schedule(
    request: CreateScheduleRequest, service: ScheduleService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Schedule created successfully", data=service.create_schedule(request))


@router.get("/me", response_model=ApiResponse[List[ScheduleResponse]])
def get_my_schedule(service: ScheduleService = Depends(), current_student: Student = Depends(get_current_student)):
    return ApiResponse(
        success=True, message="Schedule retrieved successfully", data=service.get_my_schedule(current_student)
    )


@router.get("/teacher/me", response_model=ApiResponse[List[ScheduleResponse]])
def get_my_teaching_schedule(
    service: ScheduleService = Depends(), current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Teaching schedule retrieved successfully",
        data=service.get_my_teaching_schedule(current_teacher),
    )


@router.get("/course/{course_id}", response_model=ApiResponse[List[ScheduleResponse]])
def get_schedules_by_course(
    course_id: int, service: ScheduleService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Schedule retrieved successfully", data=service.get_schedules_by_course(course_id)
    )


@router.delete("/{schedule_id}", response_model=ApiResponse[None])
def delete_schedule(schedule_id: int, service: ScheduleService = Depends(), _: User = Depends(require_role("ADMIN"))):
    service.delete_schedule(schedule_id)
    return ApiResponse(success=True, message="Schedule deleted successfully", data=None)
