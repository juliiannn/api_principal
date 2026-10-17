from datetime import datetime


def build_error_body(status_code: int, error: str, message: str, path: str) -> dict:
    """Cuerpo estándar de error: timestamp, status, error, message, path."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": status_code,
        "error": error,
        "message": message,
        "path": path,
    }
