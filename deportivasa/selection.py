"""Reglas de exclusión y selección de las mejores fotos (lógica pura, sin red)."""
import re
from collections import Counter

from . import config


def technical_reasons(item: dict) -> list[str]:
    """Motivos técnicos de exclusión, evaluables ANTES de llamar a la IA."""
    if item.get("duplicate_of"):
        return [f"duplicada exacta de {item['duplicate_of']}"]
    if item.get("incomplete"):
        return ["descarga incompleta"]
    if not item.get("valid", False):
        return [f"imagen inválida o dañada ({item.get('error', 'sin detalle')})"]
    reasons = []
    if item["short_side"] < config.MIN_SHORT_SIDE:
        reasons.append(f"resolución baja ({item['width']}x{item['height']})")
    if item["sharpness"] < config.MIN_SHARPNESS:
        reasons.append(f"poco nítida (nitidez {item['sharpness']})")
    if item.get("no_ai") and item.get("paper_ratio", 0) >= config.PAPER_RATIO_MAX:
        reasons.append(f"posible documento o planilla (detección simple sin IA, papel {item['paper_ratio']})")
    return reasons


def exclusion_reasons(item: dict) -> list[str]:
    """Lista de motivos por los que una foto NO se puede usar. Vacía = apta."""
    reasons = technical_reasons(item)
    if reasons:  # no se llega a analizar con IA
        return reasons
    analysis = item.get("analysis")
    if analysis is None:
        reasons.append(f"análisis con IA fallido ({item.get('analysis_error', 'sin detalle')})")
        return reasons
    if analysis.get("contiene_documento"):
        reasons.append("contiene documento o planilla")
    if analysis.get("datos_personales_legibles"):
        reasons.append("datos personales legibles")
    if not analysis.get("publicable"):
        reasons.append(f"no publicable según IA ({analysis.get('motivo', 'sin motivo')})")
    elif float(analysis.get("confianza", 0)) < config.MIN_CONFIDENCE:
        reasons.append(f"confianza insuficiente ({analysis.get('confianza')})")
    return reasons


def _number(name: str) -> int | None:
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else None


def base_score(item: dict) -> float:
    quality = float(item["analysis"].get("calidad", 5)) / 10
    sharp = min(item["sharpness"] / (4 * max(config.MIN_SHARPNESS, 1)), 1.0)
    return 0.6 * quality + 0.4 * sharp


def select_spread(items: list[dict], count: int) -> list[dict]:
    """Selección SIN IA: reparte las fotos aptas a lo largo de la jornada (por orden de archivo)
    y en cada tramo elige la más nítida. No juzga el contenido de la foto."""
    eligible = sorted((i for i in items if not exclusion_reasons(i)), key=lambda i: i["name"])
    n = len(eligible)
    if n <= count:
        return eligible
    picked = []
    for k in range(count):
        chunk = eligible[k * n // count:(k + 1) * n // count]
        if chunk:
            picked.append(max(chunk, key=lambda i: i["sharpness"]))
    return picked


def select(items: list[dict], count: int) -> list[dict]:
    """Elige hasta `count` fotos aptas, cuidando variedad de jugadas, camisetas y ráfagas."""
    pool = [i for i in items if not exclusion_reasons(i)]
    picked: list[dict] = []
    by_action, by_color = Counter(), Counter()

    while pool and len(picked) < count:
        def adjusted(item: dict) -> float:
            a = item["analysis"]
            score = base_score(item)
            score -= 0.08 * by_action[a.get("accion", "otro")]
            score -= 0.04 * sum(by_color[c] for c in a.get("colores_camisetas", []))
            n = _number(item["name"])
            if n is not None and any(
                (m := _number(p["name"])) is not None and abs(m - n) <= 3 for p in picked
            ):
                score -= 0.25  # evita fotos casi iguales de una misma ráfaga
            return score

        best = max(pool, key=adjusted)
        pool.remove(best)
        picked.append(best)
        by_action[best["analysis"].get("accion", "otro")] += 1
        for c in best["analysis"].get("colores_camisetas", []):
            by_color[c] += 1
    return picked
