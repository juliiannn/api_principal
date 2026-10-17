from typing import List

from fastapi import Depends

from app.dto.request.rector import CreateRectorRequest, UpdateRectorRequest
from app.dto.response.rector import RectorResponse
from app.exception import DuplicateResourceException, InvalidRequestException, ResourceNotFoundException
from app.model import Rector, UserRole
from app.repository.rector_repository import RectorRepository
from app.service.user_service import UserService


class RectorService:

    def __init__(
        self,
        rector_repository: RectorRepository = Depends(),
        user_service: UserService = Depends(),
    ):
        self.rector_repository = rector_repository
        self.user_service = user_service

    @staticmethod
    def to_response(r: Rector) -> RectorResponse:
        return RectorResponse(
            id=r.id, user_id=r.user.id, document=r.user.document, full_name=r.user.full_name,
            email=r.user.email, phone=r.user.phone, birth_date=r.user.birth_date, enabled=r.user.enabled,
            employee_code=r.employee_code, appointment_date=r.appointment_date,
            administrative_period=r.administrative_period, education_level=r.education_level,
        )

    def find_or_404(self, rector_id: int) -> Rector:
        r = self.rector_repository.find_active_by_id(rector_id)
        if r is None:
            raise ResourceNotFoundException(f"Rector with id {rector_id} not found")
        return r

    def create_rector(self, request: CreateRectorRequest) -> RectorResponse:
        if self.rector_repository.count_active_enabled() > 0:
            raise InvalidRequestException(
                "There is already an active rector; deactivate the current one before assigning a new one"
            )

        document = request.document.strip()
        email = request.email.strip().lower()
        employee_code = request.employee_code.strip()

        self.user_service.assert_identity_available(document, email)
        if self.rector_repository.exists_by_employee_code(employee_code):
            raise DuplicateResourceException("Employee code already exists")

        user = self.user_service.register_user(request, UserRole.RECTOR, document, email)

        rector = Rector(
            user_id=user.id, employee_code=employee_code, appointment_date=request.appointment_date,
            administrative_period=request.administrative_period.strip(), education_level=request.education_level,
        )
        self.rector_repository.add(rector)
        self.rector_repository.commit()
        self.rector_repository.refresh(rector)
        return self.to_response(rector)

    def get_all_rectors(self) -> List[RectorResponse]:
        return [self.to_response(r) for r in self.rector_repository.find_all_active()]

    def get_rector_by_id(self, rector_id: int) -> RectorResponse:
        return self.to_response(self.find_or_404(rector_id))

    def update_rector(self, rector_id: int, request: UpdateRectorRequest) -> RectorResponse:
        rector = self.find_or_404(rector_id)
        employee_code = request.employee_code.strip()

        if self.rector_repository.exists_by_employee_code(employee_code, exclude_id=rector_id):
            raise DuplicateResourceException("Employee code already exists")

        rector.employee_code = employee_code
        rector.appointment_date = request.appointment_date
        rector.administrative_period = request.administrative_period.strip()
        rector.education_level = request.education_level
        self.rector_repository.commit()
        self.rector_repository.refresh(rector)
        return self.to_response(rector)
