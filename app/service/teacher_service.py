from typing import List

from fastapi import Depends

from app.dto.request.teacher import CreateTeacherRequest, UpdateTeacherRequest
from app.dto.response.teacher import TeacherResponse
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import Teacher, UserRole
from app.repository.teacher_repository import TeacherRepository
from app.service.user_service import UserService


class TeacherService:

    def __init__(
        self,
        teacher_repository: TeacherRepository = Depends(),
        user_service: UserService = Depends(),
    ):
        self.teacher_repository = teacher_repository
        self.user_service = user_service

    @staticmethod
    def to_response(t: Teacher) -> TeacherResponse:
        return TeacherResponse(
            id=t.id, user_id=t.user.id, document=t.user.document, full_name=t.user.full_name,
            email=t.user.email, phone=t.user.phone, birth_date=t.user.birth_date, enabled=t.user.enabled,
            employee_code=t.employee_code, hire_date=t.hire_date, profession=t.profession,
            specialty=t.specialty, education_level=t.education_level, contract_type=t.contract_type,
        )

    def find_or_404(self, teacher_id: int) -> Teacher:
        t = self.teacher_repository.find_active_by_id(teacher_id)
        if t is None:
            raise ResourceNotFoundException(f"Teacher with id {teacher_id} not found")
        return t

    def create_teacher(self, request: CreateTeacherRequest) -> TeacherResponse:
        document = request.document.strip()
        email = request.email.strip().lower()
        employee_code = request.employee_code.strip()

        self.user_service.assert_identity_available(document, email)
        if self.teacher_repository.exists_by_employee_code(employee_code):
            raise DuplicateResourceException("Employee code already exists")

        user = self.user_service.register_user(request, UserRole.TEACHER, document, email)

        teacher = Teacher(
            user_id=user.id, employee_code=employee_code, hire_date=request.hire_date,
            profession=request.profession.strip(), specialty=request.specialty.strip(),
            education_level=request.education_level, contract_type=request.contract_type,
        )
        self.teacher_repository.add(teacher)
        self.teacher_repository.commit()
        self.teacher_repository.refresh(teacher)
        return self.to_response(teacher)

    def get_all_teachers(self) -> List[TeacherResponse]:
        return [self.to_response(t) for t in self.teacher_repository.find_all_active()]

    def get_teacher_by_id(self, teacher_id: int) -> TeacherResponse:
        return self.to_response(self.find_or_404(teacher_id))

    def update_teacher(self, teacher_id: int, request: UpdateTeacherRequest) -> TeacherResponse:
        teacher = self.find_or_404(teacher_id)
        employee_code = request.employee_code.strip()

        if self.teacher_repository.exists_by_employee_code(employee_code, exclude_id=teacher_id):
            raise DuplicateResourceException("Employee code already exists")

        teacher.employee_code = employee_code
        teacher.hire_date = request.hire_date
        teacher.profession = request.profession.strip()
        teacher.specialty = request.specialty.strip()
        teacher.education_level = request.education_level
        teacher.contract_type = request.contract_type
        self.teacher_repository.commit()
        self.teacher_repository.refresh(teacher)
        return self.to_response(teacher)
