from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import User, UserRole
from app.schemas import ApiResponse, CreateUserRequest, UpdateUserRequest, UserResponse
from app.security import hash_password
from app.utils import get_role_id

router = APIRouter(prefix="/users", tags=["Users"])


def find_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.estado.is_(True)).first()
    if user is None:
        raise ResourceNotFoundException(f"User with id {user_id} not found")
    return user


@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
def create_user(request: CreateUserRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    document = request.document.strip()
    email = request.email.strip().lower()

    if db.query(User).filter(User.document == document).first():
        raise DuplicateResourceException("Document already exists")
    if db.query(User).filter(User.email == email).first():
        raise DuplicateResourceException("Email already exists")

    user = User(
        document_type=request.document_type, document=document, email=email,
        full_name=request.full_name.strip(), phone=request.phone.strip(),
        birth_date=request.birth_date, gender=request.gender, address=request.address.strip(),
        password=hash_password(document), must_change_password=True, role_id=get_role_id(db, UserRole.ADMIN),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse(success=True, message="Admin user created successfully", data=user)


@router.get("", response_model=ApiResponse[List[UserResponse]])
def get_all_users(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    users = db.query(User).filter(User.estado.is_(True)).all()
    return ApiResponse(success=True, message="Users retrieved successfully", data=users)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user_by_id(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="User retrieved successfully", data=find_user_or_404(db, user_id))


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(user_id: int, request: UpdateUserRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    user = find_user_or_404(db, user_id)
    document = request.document.strip()
    email = request.email.strip().lower()

    if db.query(User).filter(User.document == document, User.id != user_id).first():
        raise DuplicateResourceException("Document already exists")
    if db.query(User).filter(User.email == email, User.id != user_id).first():
        raise DuplicateResourceException("Email already exists")

    user.document_type = request.document_type
    user.document = document
    user.email = email
    user.full_name = request.full_name.strip()
    user.phone = request.phone.strip()
    user.birth_date = request.birth_date
    user.gender = request.gender
    user.address = request.address.strip()
    db.commit()
    db.refresh(user)
    return ApiResponse(success=True, message="User updated successfully", data=user)


@router.put("/{user_id}/activate", response_model=ApiResponse[UserResponse])
def activate_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    user = find_user_or_404(db, user_id)
    user.enabled = True
    db.commit()
    db.refresh(user)
    return ApiResponse(success=True, message="User activated successfully", data=user)


@router.put("/{user_id}/deactivate", response_model=ApiResponse[UserResponse])
def deactivate_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    user = find_user_or_404(db, user_id)
    user.enabled = False
    db.commit()
    db.refresh(user)
    return ApiResponse(success=True, message="User deactivated successfully", data=user)


@router.put("/{user_id}/reset-password", response_model=ApiResponse[UserResponse])
def reset_password(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    user = find_user_or_404(db, user_id)
    user.password = hash_password(user.document)
    user.must_change_password = True
    db.commit()
    db.refresh(user)
    return ApiResponse(success=True, message="Password reset successfully", data=user)
