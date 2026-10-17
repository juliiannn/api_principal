from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.response.api_response import ApiResponse
from app.dto.response.statistics import (
    CourseAttendanceRateResponse, CourseStudentCountResponse, GeneralStatisticsResponse,
    SubjectAverageGradeResponse,
)
from app.model import User
from app.service.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/students-by-course", response_model=ApiResponse[List[CourseStudentCountResponse]])
def get_student_count_by_course(
    service: StatisticsService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR")),
):
    return ApiResponse(
        success=True, message="Student count by course retrieved successfully",
        data=service.get_student_count_by_course(),
    )


@router.get("/average-grades", response_model=ApiResponse[List[SubjectAverageGradeResponse]])
def get_average_grades_by_subject(
    service: StatisticsService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR")),
):
    return ApiResponse(
        success=True, message="Average grades retrieved successfully", data=service.get_average_grades_by_subject()
    )


@router.get("/attendance-rate", response_model=ApiResponse[List[CourseAttendanceRateResponse]])
def get_attendance_rate_by_course(
    service: StatisticsService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR")),
):
    return ApiResponse(
        success=True, message="Attendance rate retrieved successfully", data=service.get_attendance_rate_by_course()
    )


@router.get("/general", response_model=ApiResponse[GeneralStatisticsResponse])
def get_general_statistics(service: StatisticsService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR"))):
    return ApiResponse(
        success=True, message="General statistics retrieved successfully", data=service.get_general_statistics()
    )
