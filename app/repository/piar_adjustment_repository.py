from app.repository.base_repository import BaseRepository


class PiarAdjustmentRepository(BaseRepository):
    """Los ajustes razonables solo se crean desde el servicio de PIAR (usa save())."""
