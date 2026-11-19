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

    # ----- Correo. EMAIL_PROVIDER=smtp (Gmail u otro servidor) o brevo (API por HTTPS: sirve en Render gratis,
    #       que bloquea los puertos SMTP). Sin configurar no se envía nada: las notificaciones quedan como OMITIDO. -----
    # Nota mínima para aprobar (escala de 0 a 10). Ver app/config/grade_scale.py
    PASSING_GRADE: float = float(os.getenv("PASSING_GRADE", "6.5"))

    # ----- IA en la nube (Groq, API compatible con OpenAI). Sin GROQ_API_KEY el asistente usa la IA local o el modo básico.
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    GROQ_API_URL: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions").strip()
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "60"))
    AI_MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("AI_MAX_REQUESTS_PER_MINUTE", "6"))

    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "").strip()
    BREVO_API_URL: str = os.getenv("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email").strip()
    SMTP_HOST: str = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "").strip()               # "Colegio <notificaciones@dominio.com>"
    SMTP_SECURITY: str = os.getenv("SMTP_SECURITY", "starttls").strip().lower()   # starttls | ssl | none (solo pruebas locales)
    SMTP_TIMEOUT: int = int(os.getenv("SMTP_TIMEOUT", "20"))
    # Modo prueba: si tiene un correo, TODOS los mensajes van a esa dirección (no a los usuarios reales)
    # Seguridad en pruebas: solo se envía a estos dominios (p. ej. "gmail.com,hotmail.com"). Vacío = a cualquiera.
    # Así se usan los correos REALES de la base sin escribirle a direcciones inventadas de los datos de prueba.
    EMAIL_ALLOWED_DOMAINS: list[str] = [d.strip().lower().lstrip("@") for d in os.getenv("EMAIL_ALLOWED_DOMAINS", "").split(",") if d.strip()]
    EMAIL_REDIRECT_TO: str = os.getenv("EMAIL_REDIRECT_TO", "").strip()
    # Enlace a la aplicación que va en los correos
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")

    # ----- Reportes -----
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "storage/reports")   # almacenamiento temporal de los archivos
    REPORT_TTL_HOURS: int = int(os.getenv("REPORT_TTL_HOURS", "24"))    # horas que se conserva cada archivo
    REPORT_MAX_ROWS: int = int(os.getenv("REPORT_MAX_ROWS", "20000"))


settings = Settings()
