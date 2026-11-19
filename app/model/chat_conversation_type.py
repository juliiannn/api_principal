import enum


class ChatConversationType(str, enum.Enum):
    """GENERAL = sala donde escriben todos los conectados; DIRECT = chat privado entre dos usuarios."""
    GENERAL = "GENERAL"
    DIRECT = "DIRECT"
