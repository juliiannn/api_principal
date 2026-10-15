from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Subject, User
from app.schemas import ApiResponse, CreateSubjectRequest, SubjectResponse

router = APIRouter(prefix="/subjects", tags=["Subjects"])


def find_or_404(db: Session, subject_id: int, include_inactive: bool = False) -> Subject:
    q = db.query(Subject).filter(Subject.id == subject_id)
    if not include_inactive:
        q = q.filter(Subject.estado.is_(True))
    s = q.first()
    if s is None:
        raise ResourceNotFoundException(f"Subject with id {subject_id} not found")
    return s


@router.post("", response_model=ApiResponse[SubjectResponse], status_code=201)
def create_subject(request: CreateSubjectRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    name = request.name.strip()
    if db.query(Subject).filter(Subject.name.ilike(name)).first():
        raise DuplicateResourceException("Subject already exists")
    subject = Subject(name=name)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return ApiResponse(success=True, message="Subject created successfully", data=subject)


@router.put("/{subject_id}", response_model=ApiResponse[SubjectResponse])
def update_subject(subject_id: int, request: CreateSubjectRequest, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    subject = find_or_404(db, subject_id)
    name = request.name.strip()
    if db.query(Subject).filter(Subject.name.ilike(name), Subject.id != subject_id).first():
        raise DuplicateResourceException("Subject already exists")
    subject.name = name
    db.commit()
    db.refresh(subject)
    return ApiResponse(success=True, message="Subject updated successfully", data=subject)


@router.get("", response_model=ApiResponse[List[SubjectResponse]])
def get_all_subjects(
    include_inactive: bool = False, db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    q = db.query(Subject)
    # Solo el ADMIN puede ver las materias desactivadas (para poder reactivarlas)
    if not (include_inactive and current_user.role_ref.nombre == "ADMIN"):
        q = q.filter(Subject.estado.is_(True))
    subjects = q.all()
    return ApiResponse(success=True, message="Subjects retrieved successfully", data=subjects)


@router.get("/{subject_id}", response_model=ApiResponse[SubjectResponse])
def get_subject_by_id(subject_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    return ApiResponse(success=True, message="Subject retrieved successfully", data=find_or_404(db, subject_id))


@router.put("/{subject_id}/deactivate", response_model=ApiResponse[SubjectResponse])
def deactivate_subject(subject_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    subject = find_or_404(db, subject_id)
    subject.estado = False
    db.commit()
    db.refresh(subject)
    return ApiResponse(success=True, message="Subject deactivated successfully", data=subject)


@router.put("/{subject_id}/activate", response_model=ApiResponse[SubjectResponse])
def activate_subject(subject_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    subject = find_or_404(db, subject_id, include_inactive=True)
    subject.estado = True
    db.commit()
    db.refresh(subject)
    return ApiResponse(success=True, message="Subject activated successfully", data=subject)
