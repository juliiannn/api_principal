from app.dto.camel_model import CamelModel


class GeneralStatisticsResponse(CamelModel):
    total_students: int
    total_teachers: int
    total_coordinators: int
    active_courses: int
    total_subjects: int
