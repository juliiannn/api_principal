from pydantic import BaseModel


class SubjectResponse(BaseModel):
    id: int
    name: str
    estado: bool

    class Config:
        from_attributes = True
