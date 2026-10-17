from datetime import date as date_type
from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_teacher, require_role
from app.dto.request.attendance import CreateAttendanceRequest, CreateBulkAttendanceRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.attendance import AttendanceResponse
from app.model import Teacher, User
from app.service.attendance_service import AttendanceService

router = APIRouter(prefix="/attendances", tags=["Attendances"])


@router.post("", response_model=ApiResponse[AttendanceResponse], status_code=201)
def create_attendance(
    request: CreateAttendanceRequest, service: AttendanceService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Attendance registered successfully",
        data=service.create_attendance(request, current_teacher),
    )


@router.post("/bulk", response_model=ApiResponse[List[AttendanceResponse]], status_code=201)
def create_bulk_attendance(
    request: CreateBulkAttendanceRequest, service: AttendanceService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Attendance registered successfully for the class",
        data=service.create_bulk_attendance(request, current_teacher),
    )


@router.get("/me", response_model=ApiResponse[List[AttendanceResponse]])
def get_my_attendance(service: AttendanceService = Depends(), current_user: User = Depends(require_role("STUDENT"))):
    return ApiResponse(
        success=True, message="Attendance retrieved successfully", data=service.get_my_attendance(current_user)
    )


@router.get("/student/{student_id}", response_model=ApiResponse[List[AttendanceResponse]])
def get_attendance_by_student(
    student_id: int, service: AttendanceService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    return ApiResponse(
        success=True, message="Attendance retrieved successfully",
        data=service.get_attendance_by_student(student_id, current_user),
    )


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[AttendanceResponse]])
def get_attendance_by_course_subject_and_date(
    cs_id: int, date: date_type, service: AttendanceService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Attendance retrieved successfully",
        data=service.get_attendance_by_course_subject_and_date(cs_id, date, current_user),
    )
