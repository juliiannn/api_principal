import enum


class ContractType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    HOURLY = "HOURLY"
    TEMPORARY = "TEMPORARY"
