import enum


class PermissionScope(str, enum.Enum):
    ALL = "ALL"
    ASSIGNED = "ASSIGNED"
    OWN = "OWN"
