from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Student, User, UserRole
from app.schemas import ApiResponse, CreateStudentRequest, UpdateStudentRequest, StudentResponse
from app.security import hash_password
from app.utils import get_role_id

router = APIRouter(prefix="/students", tags=["Students"])


def to_response(s: Student) -> StudentResponse:
    return StudentResponse(
        id=s.id, user_id=s.user.id, document=s.user.document, full_name=s.user.full_name,
        email=s.user.email, phone=s.user.phone, birth_date=s.user.birth_date, enabled=s.user.enabled,
        guardian_name=s.guardian_name, guardian_phone=s.guardian_phone, guardian_email=s.guardian_email,
    )


def find_or_404(db: Session, student_id: int) -> Student:
    s = db.query(Student).filter(Student.id == student_id, Student.estado.is_(True)).first()
    if s is None:
        raise ResourceNotFoundException(f"Student with id {student_id} not found")
    return s


@router.post("", response_model=ApiResponse[StudentResponse], status_code=201)
def create_student(request: CreateStudentRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
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
        password=hash_password(document), must_change_password=True, role_id=get_role_id(db, UserRole.STUDENT),
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id, guardian_name=request.guardian_name.strip(),
        guardian_phone=request.guardian_phone.strip(), guardian_email=request.guardian_email.strip(),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return ApiResponse(success=True, message="Student created successfully", data=to_response(student))


@router.get("", response_model=ApiResponse[List[StudentResponse]])
def get_all_students(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    students = db.query(Student).filter(Student.estado.is_(True)).all()
    return ApiResponse(success=True, message="Students retrieved successfully", data=[to_response(s) for s in students])


@router.get("/me", response_model=ApiResponse[StudentResponse])
def get_my_profile(current_student: Student = Depends(get_current_student)):
    return ApiResponse(success=True, message="Profile retrieved successfully", data=to_response(current_student))


@router.get("/{student_id}", response_model=ApiResponse[StudentResponse])
def get_student_by_id(student_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    return ApiResponse(success=True, message="Student retrieved successfully", data=to_response(find_or_404(db, student_id)))


@router.put("/{student_id}", response_model=ApiResponse[StudentResponse])
def update_student(student_id: int, request: UpdateStudentRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    student = find_or_404(db, student_id)
    student.guardian_name = request.guardian_name.strip()
    student.guardian_phone = request.guardian_phone.strip()
    student.guardian_email = request.guardian_email.strip()
    db.commit()
    db.refresh(student)
    return ApiResponse(success=True, message="Student updated successfully", data=to_response(student))
