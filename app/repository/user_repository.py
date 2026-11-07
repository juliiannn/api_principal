from typing import List, Optional

from app.model import User
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def find_active_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id, User.estado.is_(True)).first()

    def find_active_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email, User.estado.is_(True)).first()

    def find_all_active(self) -> List[User]:
        return self.db.query(User).filter(User.estado.is_(True)).all()

    def exists_by_document(self, document: str) -> bool:
        return self.db.query(User).filter(User.document == document).first() is not None

    def exists_by_email(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    def exists_by_document_and_id_not(self, document: str, user_id: int) -> bool:
        return self.db.query(User).filter(User.document == document, User.id != user_id).first() is not None

    def exists_by_email_and_id_not(self, email: str, user_id: int) -> bool:
        return self.db.query(User).filter(User.email == email, User.id != user_id).first() is not None

    def exists_active_by_role_id(self, role_id: int) -> bool:
        return self.db.query(User).filter(User.role_id == role_id, User.estado.is_(True)).first() is not None
