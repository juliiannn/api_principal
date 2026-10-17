from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db


class BaseRepository:
    """Base de los repositorios: guarda la sesión y expone las operaciones de persistencia."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def add(self, entity):
        self.db.add(entity)
        return entity

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity):
        self.db.refresh(entity)
        return entity

    def save(self, entity):
        """add + commit + refresh (equivale a JpaRepository.save)."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
