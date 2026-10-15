from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, InvalidRequestException, ResourceNotFoundException
from app.models import Rector, User, UserRole
from app.schemas import ApiResponse, CreateRectorRequest, UpdateRectorRequest, RectorResponse
from app.security import hash_password
from app.utils import get_role_id

router = APIRouter(prefix="/rectors", tags=["Rectors"])


def to_response(r: Rector) -> RectorResponse:
    return RectorResponse(
        id=r.id, user_id=r.user.id, document=r.user.document, full_name=r.user.full_name,
        email=r.user.email, phone=r.user.phone, birth_date=r.user.birth_date, enabled=r.user.enabled,
        employee_code=r.employee_code, appointment_date=r.appointment_date,
        administrative_period=r.administrative_period, education_level=r.education_level,
    )


def find_or_404(db: Session, rector_id: int) -> Rector:
    r = db.query(Rector).filter(Rector.id == rector_id, Rector.estado.is_(True)).first()
    if r is None:
        raise ResourceNotFoundException(f"Rector with id {rector_id} not found")
    return r


@router.post("", response_model=ApiResponse[RectorResponse], status_code=201)
def create_rector(request: CreateRectorRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    active_rector_count = db.query(Rector).join(User, Rector.user_id == User.id).filter(User.enabled == True, Rector.estado.is_(True)).count()
    if active_rector_count > 0:
        raise InvalidRequestException("There is already an active rector; deactivate the current one before assigning a new one")

    document = request.document.strip()
    email = request.email.strip().lower()
    employee_code = request.employee_code.strip()

    if db.query(User).filter(User.document == document).first():
        raise DuplicateResourceException("Document already exists")
    if db.query(User).filter(User.email == email).first():
        raise DuplicateResourceException("Email already exists")
    if db.query(Rector).filter(Rector.employee_code == employee_code).first():
        raise DuplicateResourceException("Employee code already exists")

    user = User(
        document_type=request.document_type, document=document, email=email,
        full_name=request.full_name.strip(), phone=request.phone.strip(),
        birth_date=request.birth_date, gender=request.gender, address=request.address.strip(),
        password=hash_password(document), must_change_password=True, role_id=get_role_id(db, UserRole.RECTOR),
    )
    db.add(user)
    db.flush()

    rector = Rector(
        user_id=user.id, employee_code=employee_code, appointment_date=request.appointment_date,
        administrative_period=request.administrative_period.strip(), education_level=request.education_level,
    )
    db.add(rector)
    db.commit()
    db.refresh(rector)
    return ApiResponse(success=True, message="Rector created successfully", data=to_response(rector))


@router.get("", response_model=ApiResponse[List[RectorResponse]])
def get_all_rectors(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    rectors = db.query(Rector).filter(Rector.estado.is_(True)).all()
    return ApiResponse(success=True, message="Rectors retrieved successfully", data=[to_response(r) for r in rectors])


@router.get("/{rector_id}", response_model=ApiResponse[RectorResponse])
def get_rector_by_id(rector_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Rector retrieved successfully", data=to_response(find_or_404(db, rector_id)))


@router.put("/{rector_id}", response_model=ApiResponse[RectorResponse])
def update_rector(rector_id: int, request: UpdateRectorRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    rector = find_or_404(db, rector_id)
    employee_code = request.employee_code.strip()

    if db.query(Rector).filter(Rector.employee_code == employee_code, Rector.id != rector_id).first():
        raise DuplicateResourceException("Employee code already exists")

    rector.employee_code = employee_code
    rector.appointment_date = request.appointment_date
    rector.administrative_period = request.administrative_period.strip()
    rector.education_level = request.education_level
    db.commit()
    db.refresh(rector)
    return ApiResponse(success=True, message="Rector updated successfully", data=to_response(rector))
