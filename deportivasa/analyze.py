"""Revisión de cada foto con IA (Claude). Solo describe; no identifica personas."""
import base64
import json

import anthropic

from . import config

PROMPT = """Sos el revisor de fotos de DEPORTIVASA, una organización de torneos de fútbol amateur.
Analizá la imagen y respondé SOLO con un objeto JSON, sin texto adicional, con estos campos:

- "contiene_documento": true si se ve una planilla, lista, hoja de papel con texto, DNI, tarjeta,
  pantalla de celular o computadora con datos, o cualquier documento. false si no.
- "datos_personales_legibles": true si se alcanzan a leer nombres, números de documento,
  firmas u otros datos personales. false si no.
- "calidad": número entero de 1 a 10 (encuadre, enfoque, luz, interés de la imagen).
- "accion": una de "gol", "atajada", "remate", "disputa", "festejo", "panoramica", "retrato", "otro".
- "colores_camisetas": lista de hasta 3 colores principales de camisetas visibles (ej. ["rojo","azul"]).
- "publicable": true solo si es una foto deportiva apropiada para publicar en redes del torneo.
- "confianza": número de 0 a 1 que indica qué tan seguro estás de "publicable".
- "motivo": frase corta explicando la decisión.

Reglas: NO intentes identificar a ninguna persona ni adivinar nombres. Si hay duda sobre privacidad o
contenido sensible, poné "publicable": false y explicá el motivo."""

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=4)
    return _client


def parse_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("la respuesta no contiene JSON")
    return json.loads(text[start:end + 1])


def analyze(preview_jpeg: bytes) -> tuple[dict | None, dict, str | None]:
    """Devuelve (resultado, uso_de_tokens, error)."""
    b64 = base64.standard_b64encode(preview_jpeg).decode()
    try:
        msg = _get_client().messages.create(
            model=config.MODEL,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
        usage = {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}
        return parse_json(msg.content[0].text), usage, None
    except Exception as exc:
        return None, {"input": 0, "output": 0}, f"{type(exc).__name__}: {exc}"
