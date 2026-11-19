from app.dto.camel_model import CamelModel


class NotificationSettingUpdateRequest(CamelModel):
    activo: bool


__all__ = ["NotificationSettingUpdateRequest"]
