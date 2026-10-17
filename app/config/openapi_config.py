from fastapi import FastAPI

from app.config.settings import settings


def create_app(lifespan=None) -> FastAPI:
    """Crea la aplicación FastAPI con los metadatos de OpenAPI."""
    return FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
