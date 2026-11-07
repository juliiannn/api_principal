from app.dto.camel_model import CamelModel


class AssignDirectorTeacherRequest(CamelModel):
    teacher_id: int
