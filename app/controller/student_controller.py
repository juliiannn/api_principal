from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_student, require_role
from app.dto.request.student import CreateStudentRequest, UpdateStudentRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.student import StudentResponse
from app.model import Student, User
from app.service.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=ApiResponse[StudentResponse], status_code=201)
def create_student(
    request: CreateStudentRequest, service: StudentService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Student created successfully", data=service.create_student(request))


@router.get("", response_model=ApiResponse[List[StudentResponse]])
def get_all_students(
    service: StudentService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(success=True, message="Students retrieved successfully", data=service.get_all_students())


@router.get("/me", response_model=ApiResponse[StudentResponse])
def get_my_profile(current_student: Student = Depends(get_current_student), service: StudentService = Depends()):
    return ApiResponse(success=True, message="Profile retrieved successfully", data=service.to_response(current_student))


@router.get("/{student_id}", response_model=ApiResponse[StudentResponse])
def get_student_by_id(
    student_id: int, service: StudentService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(success=True, message="Student retrieved successfully", data=service.get_student_by_id(student_id))


@router.put("/{student_id}", response_model=ApiResponse[StudentResponse])
def update_student(
    student_id: int, request: UpdateStudentRequest,
    service: StudentService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Student updated successfully", data=service.update_student(student_id, request)
    )
