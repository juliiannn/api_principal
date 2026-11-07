from typing import List

from fastapi import Depends

from app.dto.request.special_need import CreateSpecialNeedRequest
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import SpecialNeed
from app.repository.special_need_repository import SpecialNeedRepository


class SpecialNeedService:

    def __init__(self, special_need_repository: SpecialNeedRepository = Depends()):
        self.special_need_repository = special_need_repository

    def find_or_404(self, need_id: int, include_inactive: bool = False) -> SpecialNeed:
        need = self.special_need_repository.find_by_id(need_id, include_inactive)
        if need is None:
            raise ResourceNotFoundException(f"Special need with id {need_id} not found")
        return need

    def create_special_need(self, request: CreateSpecialNeedRequest) -> SpecialNeed:
        nombre = request.nombre.strip()
        if self.special_need_repository.exists_by_name_ignore_case(nombre):
            raise DuplicateResourceException("Special need already exists")
        return self.special_need_repository.save(SpecialNeed(nombre=nombre, descripcion=request.descripcion))

    def get_all_special_needs(self, include_inactive: bool = False) -> List[SpecialNeed]:
        return self.special_need_repository.find_all(include_inactive)

    def update_special_need(self, need_id: int, request: CreateSpecialNeedRequest) -> SpecialNeed:
        need = self.find_or_404(need_id)
        nombre = request.nombre.strip()
        if self.special_need_repository.exists_by_name_ignore_case(nombre, exclude_id=need_id):
            raise DuplicateResourceException("Special need already exists")
        need.nombre, need.descripcion = nombre, request.descripcion
        self.special_need_repository.commit()
        return self.special_need_repository.refresh(need)

    def deactivate_special_need(self, need_id: int) -> SpecialNeed:
        need = self.find_or_404(need_id)
        need.estado = False
        self.special_need_repository.commit()
        return self.special_need_repository.refresh(need)

    def activate_special_need(self, need_id: int) -> SpecialNeed:
        need = self.find_or_404(need_id, include_inactive=True)
        need.estado = True
        self.special_need_repository.commit()
        return self.special_need_repository.refresh(need)
