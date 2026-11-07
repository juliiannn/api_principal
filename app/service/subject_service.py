from typing import List

from fastapi import Depends

from app.dto.request.subject import CreateSubjectRequest
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import Subject, User
from app.repository.subject_repository import SubjectRepository


class SubjectService:

    def __init__(self, subject_repository: SubjectRepository = Depends()):
        self.subject_repository = subject_repository

    def find_or_404(self, subject_id: int, include_inactive: bool = False) -> Subject:
        s = self.subject_repository.find_by_id(subject_id, include_inactive)
        if s is None:
            raise ResourceNotFoundException(f"Subject with id {subject_id} not found")
        return s

    def create_subject(self, request: CreateSubjectRequest) -> Subject:
        name = request.name.strip()
        if self.subject_repository.exists_by_name_ignore_case(name):
            raise DuplicateResourceException("Subject already exists")
        return self.subject_repository.save(Subject(name=name))

    def update_subject(self, subject_id: int, request: CreateSubjectRequest) -> Subject:
        subject = self.find_or_404(subject_id)
        name = request.name.strip()
        if self.subject_repository.exists_by_name_ignore_case(name, exclude_id=subject_id):
            raise DuplicateResourceException("Subject already exists")
        subject.name = name
        self.subject_repository.commit()
        return self.subject_repository.refresh(subject)

    def get_all_subjects(self, include_inactive: bool, current_user: User) -> List[Subject]:
        # Solo el ADMIN puede ver las materias desactivadas (para poder reactivarlas)
        show_inactive = include_inactive and current_user.role_ref.nombre == "ADMIN"
        return self.subject_repository.find_all(show_inactive)

    def get_subject_by_id(self, subject_id: int) -> Subject:
        return self.find_or_404(subject_id)

    def deactivate_subject(self, subject_id: int) -> Subject:
        subject = self.find_or_404(subject_id)
        subject.estado = False
        self.subject_repository.commit()
        return self.subject_repository.refresh(subject)

    def activate_subject(self, subject_id: int) -> Subject:
        subject = self.find_or_404(subject_id, include_inactive=True)
        subject.estado = True
        self.subject_repository.commit()
        return self.subject_repository.refresh(subject)
