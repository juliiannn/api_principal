import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Variables de entorno (equivale a application.yml de Spring)."""

    APP_NAME: str = "Colegio API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))

    CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]


settings = Settings()
