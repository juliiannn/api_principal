from typing import List

from fastapi import Depends

from app.dto.request.announcement import CreateAnnouncementRequest
from app.dto.response.announcement import AnnouncementResponse
from app.exception import ResourceNotFoundException
from app.model import Announcement, User
from app.repository.announcement_repository import AnnouncementRepository


class AnnouncementService:
    """Comunicados institucionales: los publica el rector (o el administrador) y los ven todos los roles."""

    def __init__(self, announcement_repository: AnnouncementRepository = Depends()):
        self.announcement_repository = announcement_repository

    @staticmethod
    def to_response(a: Announcement) -> AnnouncementResponse:
        return AnnouncementResponse(
            id=a.id, titulo=a.titulo, contenido=a.contenido, publicado_por_nombre=a.author.full_name,
            publicado_por_rol=a.author.role_ref.nombre, creado=a.creado, actualizado=a.actualizado,
            estado=a.estado,
        )

    def find_or_404(self, announcement_id: int) -> Announcement:
        a = self.announcement_repository.find_active_by_id(announcement_id)
        if a is None:
            raise ResourceNotFoundException(f"Announcement with id {announcement_id} not found")
        return a

    def create_announcement(self, request: CreateAnnouncementRequest, current_user: User) -> AnnouncementResponse:
        announcement = Announcement(
            titulo=request.titulo.strip(), contenido=request.contenido.strip(), publicado_por=current_user.id
        )
        return self.to_response(self.announcement_repository.save(announcement))

    def get_all_announcements(self) -> List[AnnouncementResponse]:
        return [self.to_response(a) for a in self.announcement_repository.find_all_active()]

    def get_announcement_by_id(self, announcement_id: int) -> AnnouncementResponse:
        return self.to_response(self.find_or_404(announcement_id))

    def update_announcement(self, announcement_id: int, request: CreateAnnouncementRequest) -> AnnouncementResponse:
        announcement = self.find_or_404(announcement_id)
        announcement.titulo = request.titulo.strip()
        announcement.contenido = request.contenido.strip()
        self.announcement_repository.commit()
        self.announcement_repository.refresh(announcement)
        return self.to_response(announcement)

    def deactivate_announcement(self, announcement_id: int) -> AnnouncementResponse:
        announcement = self.find_or_404(announcement_id)
        announcement.estado = False
        self.announcement_repository.commit()
        self.announcement_repository.refresh(announcement)
        return self.to_response(announcement)
