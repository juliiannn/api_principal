import enum


class DocumentType(str, enum.Enum):
    TI = "TI"
    CC = "CC"
    CE = "CE"
    PASSPORT = "PASSPORT"
