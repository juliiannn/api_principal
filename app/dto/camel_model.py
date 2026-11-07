from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base de todos los DTO: el JSON viaja en camelCase (accessToken, fullName, studentId...)
    como lo usa el frontend Angular, y en Python los campos siguen en snake_case.
    populate_by_name=True permite construir el DTO también con el nombre snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
