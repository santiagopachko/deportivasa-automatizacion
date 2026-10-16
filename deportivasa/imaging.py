"""Controles técnicos de cada imagen."""
import io

import numpy as np
from PIL import Image, ImageOps


def laplacian_variance(gray: np.ndarray) -> float:
    """Medida simple de nitidez: más alto = más nítida."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    c = gray[1:-1, 1:-1]
    lap = gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4 * c
    return float(lap.var())


def inspect(data: bytes, max_side: int = 1024) -> dict:
    """Valida que la imagen abra completa y calcula tamaño, nitidez y vista reducida."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:  # archivo dañado o incompleto
        return {"valid": False, "error": f"{type(exc).__name__}: {exc}"}

    img = ImageOps.exif_transpose(img).convert("RGB")
    width, height = img.size
    small = img.copy()
    small.thumbnail((max_side, max_side))
    gray = np.asarray(small.convert("L"), dtype=np.float32)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=80)
    return {
        "valid": True,
        "width": width,
        "height": height,
        "short_side": min(width, height),
        "sharpness": round(laplacian_variance(gray), 1),
        "preview_jpeg": buf.getvalue(),
    }
