import enum


class DocumentType(str, enum.Enum):
    RC = "RC"   # registro civil (menores de 7 años)
    TI = "TI"
    CC = "CC"
    CE = "CE"
    PASSPORT = "PASSPORT"
