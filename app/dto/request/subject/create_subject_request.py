from pydantic import BaseModel


class CreateSubjectRequest(BaseModel):
    name: str
