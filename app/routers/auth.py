from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_user_permissions
from app.exceptions import InvalidCredentialsException, InvalidRequestException
from app.models import User
from app.schemas import ApiResponse, LoginRequest, TokenResponse, ChangePasswordRequest, MyPermissionResponse
from app.security import verify_password, hash_password, create_access_token, JWT_EXPIRATION_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email, User.estado.is_(True)).first()

    if user is None or not user.enabled or not user.role_ref.estado or not verify_password(request.password, user.password):
        raise InvalidCredentialsException("Invalid credentials")

    token = create_access_token(email=user.email, role=user.role.value)

    return ApiResponse(
        success=True, message="Login successful",
        data=TokenResponse(
            access_token=token, expires_in=JWT_EXPIRATION_MINUTES * 60,
            must_change_password=user.must_change_password, role=user.role,
        ),
    )


@router.put("/change-password", response_model=ApiResponse[None])
def change_password(
    request: ChangePasswordRequest, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(request.current_password, current_user.password):
        raise InvalidCredentialsException("Current password is incorrect")
    if verify_password(request.new_password, current_user.password):
        raise InvalidRequestException("New password must be different from the current password")

    current_user.password = hash_password(request.new_password)
    current_user.must_change_password = False
    db.commit()

    return ApiResponse(success=True, message="Password changed successfully", data=None)


@router.get("/me/permissions", response_model=ApiResponse[List[MyPermissionResponse]])
def get_my_permissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Módulos y permisos del usuario autenticado (sirve para armar el menú del frontend)."""
    permissions = get_user_permissions(db, current_user)
    data = [
        MyPermissionResponse(
            modulo=p.module.nombre, ruta=p.module.ruta, puede_ver=p.puede_ver, puede_crear=p.puede_crear,
            puede_editar=p.puede_editar, puede_eliminar=p.puede_eliminar, alcance=p.alcance,
        )
        for p in permissions
    ]
    return ApiResponse(success=True, message="Permissions retrieved successfully", data=data)
