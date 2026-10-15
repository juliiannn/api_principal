from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Coordinator, User, UserRole
from app.schemas import ApiResponse, CreateCoordinatorRequest, UpdateCoordinatorRequest, CoordinatorResponse
from app.security import hash_password
from app.utils import get_role_id

router = APIRouter(prefix="/coordinators", tags=["Coordinators"])


def to_response(c: Coordinator) -> CoordinatorResponse:
    return CoordinatorResponse(
        id=c.id, user_id=c.user.id, document=c.user.document, full_name=c.user.full_name,
        email=c.user.email, phone=c.user.phone, birth_date=c.user.birth_date, enabled=c.user.enabled,
        employee_code=c.employee_code, area=c.area, assignment_date=c.assignment_date,
        education_level=c.education_level,
    )


def find_or_404(db: Session, coordinator_id: int) -> Coordinator:
    c = db.query(Coordinator).filter(Coordinator.id == coordinator_id, Coordinator.estado.is_(True)).first()
    if c is None:
        raise ResourceNotFoundException(f"Coordinator with id {coordinator_id} not found")
    return c


@router.post("", response_model=ApiResponse[CoordinatorResponse], status_code=201)
def create_coordinator(request: CreateCoordinatorRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    document = request.document.strip()
    email = request.email.strip().lower()
    employee_code = request.employee_code.strip()

    if db.query(User).filter(User.document == document).first():
        raise DuplicateResourceException("Document already exists")
    if db.query(User).filter(User.email == email).first():
        raise DuplicateResourceException("Email already exists")
    if db.query(Coordinator).filter(Coordinator.employee_code == employee_code).first():
        raise DuplicateResourceException("Employee code already exists")

    user = User(
        document_type=request.document_type, document=document, email=email,
        full_name=request.full_name.strip(), phone=request.phone.strip(),
        birth_date=request.birth_date, gender=request.gender, address=request.address.strip(),
        password=hash_password(document), must_change_password=True, role_id=get_role_id(db, UserRole.COORDINATOR),
    )
    db.add(user)
    db.flush()

    coordinator = Coordinator(
        user_id=user.id, employee_code=employee_code, area=request.area,
        assignment_date=request.assignment_date, education_level=request.education_level,
    )
    db.add(coordinator)
    db.commit()
    db.refresh(coordinator)
    return ApiResponse(success=True, message="Coordinator created successfully", data=to_response(coordinator))


@router.get("", response_model=ApiResponse[List[CoordinatorResponse]])
def get_all_coordinators(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    coordinators = db.query(Coordinator).filter(Coordinator.estado.is_(True)).all()
    return ApiResponse(success=True, message="Coordinators retrieved successfully", data=[to_response(c) for c in coordinators])


@router.get("/{coordinator_id}", response_model=ApiResponse[CoordinatorResponse])
def get_coordinator_by_id(coordinator_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    return ApiResponse(success=True, message="Coordinator retrieved successfully", data=to_response(find_or_404(db, coordinator_id)))


@router.put("/{coordinator_id}", response_model=ApiResponse[CoordinatorResponse])
def update_coordinator(coordinator_id: int, request: UpdateCoordinatorRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    coordinator = find_or_404(db, coordinator_id)
    employee_code = request.employee_code.strip()

    if db.query(Coordinator).filter(Coordinator.employee_code == employee_code, Coordinator.id != coordinator_id).first():
        raise DuplicateResourceException("Employee code already exists")

    coordinator.employee_code = employee_code
    coordinator.area = request.area
    coordinator.assignment_date = request.assignment_date
    coordinator.education_level = request.education_level
    db.commit()
    db.refresh(coordinator)
    return ApiResponse(success=True, message="Coordinator updated successfully", data=to_response(coordinator))
