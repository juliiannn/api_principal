from typing import List

from fastapi import Depends

from app.dto.request.coordinator import CreateCoordinatorRequest, UpdateCoordinatorRequest
from app.dto.response.coordinator import CoordinatorResponse
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import Coordinator, UserRole
from app.repository.coordinator_repository import CoordinatorRepository
from app.service.user_service import UserService


class CoordinatorService:

    def __init__(
        self,
        coordinator_repository: CoordinatorRepository = Depends(),
        user_service: UserService = Depends(),
    ):
        self.coordinator_repository = coordinator_repository
        self.user_service = user_service

    @staticmethod
    def to_response(c: Coordinator) -> CoordinatorResponse:
        return CoordinatorResponse(
            id=c.id, user_id=c.user.id, document=c.user.document, full_name=c.user.full_name,
            email=c.user.email, phone=c.user.phone, birth_date=c.user.birth_date, enabled=c.user.enabled,
            employee_code=c.employee_code, area=c.area, assignment_date=c.assignment_date,
            education_level=c.education_level,
        )

    def find_or_404(self, coordinator_id: int) -> Coordinator:
        c = self.coordinator_repository.find_active_by_id(coordinator_id)
        if c is None:
            raise ResourceNotFoundException(f"Coordinator with id {coordinator_id} not found")
        return c

    def create_coordinator(self, request: CreateCoordinatorRequest) -> CoordinatorResponse:
        document = request.document.strip()
        email = request.email.strip().lower()
        employee_code = request.employee_code.strip()

        self.user_service.assert_identity_available(document, email)
        if self.coordinator_repository.exists_by_employee_code(employee_code):
            raise DuplicateResourceException("Employee code already exists")

        user = self.user_service.register_user(request, UserRole.COORDINATOR, document, email)

        coordinator = Coordinator(
            user_id=user.id, employee_code=employee_code, area=request.area,
            assignment_date=request.assignment_date, education_level=request.education_level,
        )
        self.coordinator_repository.add(coordinator)
        self.coordinator_repository.commit()
        self.coordinator_repository.refresh(coordinator)
        return self.to_response(coordinator)

    def get_all_coordinators(self) -> List[CoordinatorResponse]:
        return [self.to_response(c) for c in self.coordinator_repository.find_all_active()]

    def get_coordinator_by_id(self, coordinator_id: int) -> CoordinatorResponse:
        return self.to_response(self.find_or_404(coordinator_id))

    def update_coordinator(self, coordinator_id: int, request: UpdateCoordinatorRequest) -> CoordinatorResponse:
        coordinator = self.find_or_404(coordinator_id)
        employee_code = request.employee_code.strip()

        if self.coordinator_repository.exists_by_employee_code(employee_code, exclude_id=coordinator_id):
            raise DuplicateResourceException("Employee code already exists")

        coordinator.employee_code = employee_code
        coordinator.area = request.area
        coordinator.assignment_date = request.assignment_date
        coordinator.education_level = request.education_level
        self.coordinator_repository.commit()
        self.coordinator_repository.refresh(coordinator)
        return self.to_response(coordinator)
