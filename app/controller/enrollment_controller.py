from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.enrollment import CreateEnrollmentRequest, TransferEnrollmentRequest, UpdateEnrollmentStatusRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.enrollment import EnrollmentResponse
from app.dto.response.student import StudentResponse
from app.model import User
from app.service.enrollment_service import EnrollmentService

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("", response_model=ApiResponse[EnrollmentResponse], status_code=201)
def create_enrollment(
    request: CreateEnrollmentRequest, service: EnrollmentService = Depends(),
    _: User = Depends(require_role("ADMIN", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Enrollment created successfully", data=service.create_enrollment(request)
    )


@router.put("/transfer", response_model=ApiResponse[EnrollmentResponse])
def transfer_student(
    request: TransferEnrollmentRequest, service: EnrollmentService = Depends(),
    _: User = Depends(require_role("ADMIN", "COORDINATOR")),
):
    return ApiResponse(success=True, message="Student transferred successfully", data=service.transfer_student(request))


@router.get("", response_model=ApiResponse[List[EnrollmentResponse]])
def get_all_enrollments(
    service: EnrollmentService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Enrollments retrieved successfully", data=service.get_all_enrollments()
    )


@router.get("/{enrollment_id}", response_model=ApiResponse[EnrollmentResponse])
def get_enrollment_by_id(
    enrollment_id: int, service: EnrollmentService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Enrollment retrieved successfully", data=service.get_enrollment_by_id(enrollment_id)
    )


@router.get("/course/{course_id}/students", response_model=ApiResponse[List[StudentResponse]])
def get_students_by_course(
    course_id: int, service: EnrollmentService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Students retrieved successfully",
        data=service.get_students_by_course(course_id, current_user),
    )


@router.put("/{enrollment_id}/cancel", response_model=ApiResponse[EnrollmentResponse])
def cancel_enrollment(
    enrollment_id: int, service: EnrollmentService = Depends(),
    _: User = Depends(require_role("ADMIN", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Enrollment cancelled successfully", data=service.cancel_enrollment(enrollment_id)
    )


@router.put("/{enrollment_id}/status", response_model=ApiResponse[EnrollmentResponse])
def update_status(
    enrollment_id: int, request: UpdateEnrollmentStatusRequest, service: EnrollmentService = Depends(),
    _: User = Depends(require_role("ADMIN", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Enrollment status updated successfully",
        data=service.update_status(enrollment_id, request),
    )
