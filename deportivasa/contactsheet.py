"""Hoja de contactos: una sola imagen con las fotos elegidas, numeradas, para revisarlas de un vistazo."""
import io

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # versiones viejas de Pillow
        return ImageFont.load_default()


def build(selected: list[dict], cols: int = 4, thumb_w: int = 360, thumb_h: int = 270, pad: int = 8) -> bytes:
    """Devuelve un JPEG con las miniaturas numeradas igual que en el informe (1, 2, 3...)."""
    rows = max(1, (len(selected) + cols - 1) // cols)
    width = cols * (thumb_w + pad) + pad
    height = rows * (thumb_h + pad) + pad
    sheet = Image.new("RGB", (width, height), (20, 24, 36))
    draw = ImageDraw.Draw(sheet)
    font = _font(28)

    for i, item in enumerate(selected):
        im = Image.open(io.BytesIO(item["preview"])).convert("RGB")
        im.thumbnail((thumb_w, thumb_h))
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + pad)
        sheet.paste(im, (x + (thumb_w - im.width) // 2, y + (thumb_h - im.height) // 2))
        draw.rectangle([x, y, x + 56, y + 40], fill=(0, 70, 160))
        draw.text((x + 8, y + 4), str(i + 1), fill="white", font=font)

    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=82)
    return buf.getvalue()
