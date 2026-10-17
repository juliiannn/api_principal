import enum


class EducationLevel(str, enum.Enum):
    BACHELOR = "BACHELOR"
    UNDERGRADUATE = "UNDERGRADUATE"
    SPECIALIST = "SPECIALIST"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"
