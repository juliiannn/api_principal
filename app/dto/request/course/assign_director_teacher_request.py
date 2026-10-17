from pydantic import BaseModel


class AssignDirectorTeacherRequest(BaseModel):
    teacher_id: int
