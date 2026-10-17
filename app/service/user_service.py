from typing import List

from fastapi import Depends

from app.config.security_config import hash_password
from app.dto.request.person import BasePersonRequest
from app.dto.request.user import CreateUserRequest, UpdateUserRequest
from app.exception import DuplicateResourceException, InvalidRequestException, ResourceNotFoundException
from app.model import User, UserRole
from app.repository.role_repository import RoleRepository
from app.repository.user_repository import UserRepository


class UserService:

    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        role_repository: RoleRepository = Depends(),
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository

    # ----- utilidades compartidas con los servicios de perfiles -----

    def get_role_id(self, role: UserRole) -> int:
        """Devuelve el id del rol (tabla roles) a partir de su nombre. Se usa al crear usuarios."""
        found = self.role_repository.find_active_by_name(role.value)
        if found is None:
            raise InvalidRequestException(f"El rol {role.value} no existe o está inactivo")
        return found.id

    def assert_identity_available(self, document: str, email: str) -> None:
        if self.user_repository.exists_by_document(document):
            raise DuplicateResourceException("Document already exists")
        if self.user_repository.exists_by_email(email):
            raise DuplicateResourceException("Email already exists")

    def register_user(self, request: BasePersonRequest, role: UserRole, document: str, email: str) -> User:
        """Crea el usuario base (sin commit): la contraseña inicial es el documento."""
        user = User(
            document_type=request.document_type, document=document, email=email,
            full_name=request.full_name.strip(), phone=request.phone.strip(),
            birth_date=request.birth_date, gender=request.gender, address=request.address.strip(),
            password=hash_password(document), must_change_password=True, role_id=self.get_role_id(role),
        )
        self.user_repository.add(user)
        self.user_repository.flush()
        return user

    # ----- casos de uso -----

    def find_or_404(self, user_id: int) -> User:
        user = self.user_repository.find_active_by_id(user_id)
        if user is None:
            raise ResourceNotFoundException(f"User with id {user_id} not found")
        return user

    def create_user(self, request: CreateUserRequest) -> User:
        document = request.document.strip()
        email = request.email.strip().lower()
        self.assert_identity_available(document, email)
        user = self.register_user(request, UserRole.ADMIN, document, email)
        self.user_repository.commit()
        return self.user_repository.refresh(user)

    def get_all_users(self) -> List[User]:
        return self.user_repository.find_all_active()

    def get_user_by_id(self, user_id: int) -> User:
        return self.find_or_404(user_id)

    def update_user(self, user_id: int, request: UpdateUserRequest) -> User:
        user = self.find_or_404(user_id)
        document = request.document.strip()
        email = request.email.strip().lower()

        if self.user_repository.exists_by_document_and_id_not(document, user_id):
            raise DuplicateResourceException("Document already exists")
        if self.user_repository.exists_by_email_and_id_not(email, user_id):
            raise DuplicateResourceException("Email already exists")

        user.document_type = request.document_type
        user.document = document
        user.email = email
        user.full_name = request.full_name.strip()
        user.phone = request.phone.strip()
        user.birth_date = request.birth_date
        user.gender = request.gender
        user.address = request.address.strip()
        self.user_repository.commit()
        return self.user_repository.refresh(user)

    def set_enabled(self, user_id: int, enabled: bool) -> User:
        user = self.find_or_404(user_id)
        user.enabled = enabled
        self.user_repository.commit()
        return self.user_repository.refresh(user)

    def reset_password(self, user_id: int) -> User:
        user = self.find_or_404(user_id)
        user.password = hash_password(user.document)
        user.must_change_password = True
        self.user_repository.commit()
        return self.user_repository.refresh(user)
