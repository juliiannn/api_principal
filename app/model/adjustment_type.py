import enum


class AdjustmentType(str, enum.Enum):
    ACCESS = "ACCESS"
    CURRICULAR = "CURRICULAR"
    METHODOLOGICAL = "METHODOLOGICAL"
    EVALUATIVE = "EVALUATIVE"
