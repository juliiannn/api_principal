from typing import Generic, Optional, TypeVar
from app.dto.camel_model import CamelModel


T = TypeVar("T")


class ApiResponse(CamelModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
