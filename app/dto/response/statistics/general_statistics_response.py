from pydantic import BaseModel


class GeneralStatisticsResponse(BaseModel):
    total_students: int
    total_teachers: int
    total_coordinators: int
    active_courses: int
    total_subjects: int
