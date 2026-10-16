"""Detección de cargas completas y huella del lote (lógica pura, sin red)."""
import hashlib
from datetime import datetime, timedelta, timezone


def parse_time(value: str) -> datetime:
    """Convierte '2026-10-15T23:15:18.436Z' en datetime con zona horaria."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_stable(files: list[dict], now: datetime, minutes: int) -> bool:
    """True si no llegaron archivos nuevos en los últimos `minutes` minutos.

    Se usa createdTime (cuando el archivo llegó a Drive), no modifiedTime,
    porque modifiedTime suele conservar la fecha original de la cámara.
    """
    if not files:
        return False
    newest = max(parse_time(f["createdTime"]) for f in files)
    return now - newest >= timedelta(minutes=minutes)


def minutes_since_last_upload(files: list[dict], now: datetime) -> float | None:
    if not files:
        return None
    newest = max(parse_time(f["createdTime"]) for f in files)
    return (now - newest).total_seconds() / 60


def fingerprint(files: list[dict]) -> str:
    """Huella del contenido del lote. Cambia si se agregan o quitan fotos."""
    ids = sorted(f["id"] for f in files)
    return hashlib.sha1("|".join(ids).encode()).hexdigest()
