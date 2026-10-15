from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_teacher, require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Teacher, User, UserRole
from app.schemas import ApiResponse, CreateTeacherRequest, UpdateTeacherRequest, TeacherResponse
from app.security import hash_password
from app.utils import get_role_id

router = APIRouter(prefix="/teachers", tags=["Teachers"])


def to_response(t: Teacher) -> TeacherResponse:
    return TeacherResponse(
        id=t.id, user_id=t.user.id, document=t.user.document, full_name=t.user.full_name,
        email=t.user.email, phone=t.user.phone, birth_date=t.user.birth_date, enabled=t.user.enabled,
        employee_code=t.employee_code, hire_date=t.hire_date, profession=t.profession,
        specialty=t.specialty, education_level=t.education_level, contract_type=t.contract_type,
    )


def find_or_404(db: Session, teacher_id: int) -> Teacher:
    t = db.query(Teacher).filter(Teacher.id == teacher_id, Teacher.estado.is_(True)).first()
    if t is None:
        raise ResourceNotFoundException(f"Teacher with id {teacher_id} not found")
    return t


@router.post("", response_model=ApiResponse[TeacherResponse], status_code=201)
def create_teacher(request: CreateTeacherRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    document = request.document.strip()
    email = request.email.strip().lower()
    employee_code = request.employee_code.strip()

    if db.query(User).filter(User.document == document).first():
        raise DuplicateResourceException("Document already exists")
    if db.query(User).filter(User.email == email).first():
        raise DuplicateResourceException("Email already exists")
    if db.query(Teacher).filter(Teacher.employee_code == employee_code).first():
        raise DuplicateResourceException("Employee code already exists")

    user = User(
        document_type=request.document_type, document=document, email=email,
        full_name=request.full_name.strip(), phone=request.phone.strip(),
        birth_date=request.birth_date, gender=request.gender, address=request.address.strip(),
        password=hash_password(document), must_change_password=True, role_id=get_role_id(db, UserRole.TEACHER),
    )
    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id, employee_code=employee_code, hire_date=request.hire_date,
        profession=request.profession.strip(), specialty=request.specialty.strip(),
        education_level=request.education_level, contract_type=request.contract_type,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return ApiResponse(success=True, message="Teacher created successfully", data=to_response(teacher))


@router.get("", response_model=ApiResponse[List[TeacherResponse]])
def get_all_teachers(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    teachers = db.query(Teacher).filter(Teacher.estado.is_(True)).all()
    return ApiResponse(success=True, message="Teachers retrieved successfully", data=[to_response(t) for t in teachers])


@router.get("/me", response_model=ApiResponse[TeacherResponse])
def get_my_profile(current_teacher: Teacher = Depends(get_current_teacher)):
    return ApiResponse(success=True, message="Profile retrieved successfully", data=to_response(current_teacher))


@router.get("/{teacher_id}", response_model=ApiResponse[TeacherResponse])
def get_teacher_by_id(teacher_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    return ApiResponse(success=True, message="Teacher retrieved successfully", data=to_response(find_or_404(db, teacher_id)))


@router.put("/{teacher_id}", response_model=ApiResponse[TeacherResponse])
def update_teacher(teacher_id: int, request: UpdateTeacherRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    teacher = find_or_404(db, teacher_id)
    employee_code = request.employee_code.strip()

    if db.query(Teacher).filter(Teacher.employee_code == employee_code, Teacher.id != teacher_id).first():
        raise DuplicateResourceException("Employee code already exists")

    teacher.employee_code = employee_code
    teacher.hire_date = request.hire_date
    teacher.profession = request.profession.strip()
    teacher.specialty = request.specialty.strip()
    teacher.education_level = request.education_level
    teacher.contract_type = request.contract_type
    db.commit()
    db.refresh(teacher)
    return ApiResponse(success=True, message="Teacher updated successfully", data=to_response(teacher))
