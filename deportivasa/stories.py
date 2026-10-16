"""Plantilla de historias de Instagram (1080x1920): foto a pantalla completa, sin retoques de color."""
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
_DIR = "/usr/share/fonts/truetype/dejavu/"


def _font(name: str, size: int):
    try:
        return ImageFont.truetype(_DIR + name, size)
    except OSError:
        return ImageFont.load_default(size=size)


def _cover(photo: Image.Image) -> Image.Image:
    """Escala la foto para cubrir todo el cuadro (recorte centrado). Solo reduce, no agranda de más."""
    s = max(W / photo.width, H / photo.height)
    p = photo.resize((round(photo.width * s), round(photo.height * s)), Image.LANCZOS)
    left, top = (p.width - W) // 2, (p.height - H) // 2
    return p.crop((left, top, left + W, top + H))


def _spaced(d, text, cx, y, font, fill, spacing):
    width = sum(d.textlength(c, font=font) + spacing for c in text) - spacing
    x = cx - width / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill)
        x += d.textlength(c, font=font) + spacing


def build_story(photo_bytes: bytes, fecha: str, torneo_corto: str, final: bool = False) -> bytes:
    photo = ImageOps.exif_transpose(Image.open(io.BytesIO(photo_bytes))).convert("RGB")
    im = _cover(photo)

    # Degradado suave solo para que el texto se lea; no toca el color de la foto en el resto del cuadro.
    y = np.arange(H, dtype=np.float32)[:, None]
    g = np.clip((y - 1150) / 770, 0, 1) ** 1.3 * 0.80 + np.clip((300 - y) / 300, 0, 1) ** 1.5 * 0.35
    alpha = np.repeat(np.clip(g, 0, 1), W, axis=1)[..., None]
    dark = np.array([6, 14, 34], dtype=np.float32)
    arr = np.asarray(im).astype(np.float32) * (1 - alpha) + dark * alpha
    im = Image.fromarray(arr.astype(np.uint8))

    d = ImageDraw.Draw(im)
    cx = W // 2
    azul = (140, 185, 255)
    bold, light, reg = "DejaVuSansCondensed-Bold.ttf", "DejaVuSans-ExtraLight.ttf", "DejaVuSansCondensed.ttf"
    _spaced(d, "DEPORTIVASA", cx, 215, _font(bold, 30), "white", 12)
    d.line([cx - 30, 275, cx + 30, 275], fill=azul, width=3)

    kicker = "TODAS LAS FOTOS" if final else "FOTOS DE LA"
    _spaced(d, kicker, cx, 1330, _font(bold, 40), azul, 10)
    big = _font(light, 180)
    titulo = fecha.upper()
    d.text((cx - d.textlength(titulo, font=big) / 2, 1380), titulo, font=big, fill="white")
    _spaced(d, torneo_corto.upper(), cx, 1640, _font(reg, 34), (230, 236, 247), 8)
    if final:
        bw = 620
        d.rounded_rectangle([cx - bw / 2, 1730, cx + bw / 2, 1810], 40, fill="white")
        _spaced(d, "LINK EN LA BIO", cx, 1754, _font(bold, 32), (8, 50, 130), 8)

    out = io.BytesIO()
    im.save(out, "JPEG", quality=95, subsampling=0, optimize=True)
    return out.getvalue()
