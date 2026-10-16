"""Informe del lote: archivo Markdown en el repositorio y mail de resumen."""
import os
import smtplib
from collections import Counter
from datetime import datetime
from email.message import EmailMessage
from html import escape


NO_AI_WARNING = (
    "SIN REVISIÓN CON IA: la privacidad (DNI, planillas, datos personales) solo se controló con una "
    "detección simple y aproximada, y la elección se hizo por nitidez y reparto a lo largo de la jornada. "
    "REVISAR A MANO antes de publicar."
)


def build_markdown(batch: dict, items: list[dict], selected: list[dict], reasons: dict, usage: dict,
                   use_ai: bool = True) -> str:
    excluded = [i for i in items if reasons[i["id"]]]
    counts = Counter(r.split(" (")[0] for i in excluded for r in reasons[i["id"]])
    lines = [
        f"# {batch['tournament']} — {batch['fecha']} (MODO PRUEBA, no se publicó nada)",
        "",
        *([] if use_ai else [f"> **ATENCIÓN: {NO_AI_WARNING}**", ""]),
        f"- Fotos encontradas: {len(items)}",
        f"- Elegidas: {len(selected)}",
        f"- Excluidas: {len(excluded)}",
        f"- Tokens usados por la IA: {usage['input']} de entrada y {usage['output']} de salida",
        "",
        "## Fotos elegidas",
    ]
    for i, item in enumerate(selected, 1):
        a = item["analysis"]
        lines.append(
            f"{i}. [{item['name']}]({item.get('webViewLink', '')}) — {a.get('accion')}, "
            f"calidad {a.get('calidad')}, nitidez {item['sharpness']}, confianza {a.get('confianza')}"
        )
    lines += ["", "## Motivos de exclusión (resumen)"]
    lines += [f"- {k}: {v}" for k, v in counts.most_common()] or ["- ninguna"]
    lines += ["", "## Detalle de excluidas"]
    for item in excluded:
        lines.append(f"- {item['name']}: {'; '.join(reasons[item['id']])}")
    return "\n".join(lines) + "\n"


def build_html(batch: dict, items: list[dict], selected: list[dict], reasons: dict, usage: dict,
               use_ai: bool = True) -> str:
    excluded = [i for i in items if reasons[i["id"]]]
    rows = "".join(
        f"<li><a href=\"{escape(i.get('webViewLink', ''))}\">{escape(i['name'])}</a> — "
        f"{escape(str(i['analysis'].get('accion')))}, calidad {i['analysis'].get('calidad')}</li>"
        for i in selected
    )
    dudosas = "".join(
        f"<li>{escape(i['name'])}: {escape('; '.join(reasons[i['id']]))}</li>" for i in excluded[:40]
    )
    more = f"<p>(y {len(excluded) - 40} más en el informe completo del repositorio)</p>" if len(excluded) > 40 else ""
    return f"""<h2>{escape(batch['tournament'])} — {escape(batch['fecha'])}</h2>
<p><b>MODO PRUEBA:</b> no se publicó ni se borró nada.</p>
{'' if use_ai else '<p><b>ATENCIÓN: ' + escape(NO_AI_WARNING) + '</b></p>'}
<p>Encontradas: {len(items)} · Elegidas: {len(selected)} · Excluidas: {len(excluded)}<br>
Tokens de IA: {usage['input']} entrada / {usage['output']} salida</p>
<h3>Fotos elegidas</h3><ol>{rows}</ol>
<h3>Excluidas (con motivo)</h3><ul>{dudosas}</ul>{more}"""


def send_mail(subject: str, html: str) -> str:
    """Envía el resumen por Gmail. Si faltan los datos, no falla: lo avisa."""
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("MAIL_TO")
    if not (user and password and to):
        return "mail omitido: faltan GMAIL_USER, GMAIL_APP_PASSWORD o MAIL_TO"
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.set_content("Este resumen requiere un cliente de mail con formato HTML.")
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return "mail enviado"
    except Exception as exc:
        return f"mail NO enviado: {type(exc).__name__}: {exc}"


def venue_for(tournament: str) -> str:
    """Sede según el torneo (datos del informe de DEPORTIVASA)."""
    t = tournament.upper()
    if "LUGANO" in t:
        return "SER FÚTBOL JD LUGANO"
    if "PORVENIR" in t:
        return "EL PORVENIR DE GERLI"
    return ""


def build_caption(batch: dict) -> str:
    """Texto institucional de referencia. No inventa resultados, goleadores ni fechas de calendario."""
    fecha = batch["fecha"].title()  # "FECHA 04" -> "Fecha 04"
    venue = venue_for(batch["tournament"])
    lines = [
        "¡Así se vivió una nueva fecha de DEPORTIVASA! ⚽🔵⚪",
        "Te compartimos algunos de los mejores momentos de la jornada.",
    ]
    if venue:
        lines.append(f"📍 {venue}")
    lines += [f"🏆 {batch['tournament']}", f"📅 {fecha}", "DEPORTIVASA — Donde el deporte se vive."]
    return "\n".join(lines)


def build_publish_list(batch: dict, selected: list[dict], now: datetime, group_size: int = 10) -> dict:
    """Lista para publicar con el OK de Santiago. La numeración coincide con la hoja de contactos."""
    photos = [
        {"n": n, "name": i["name"], "file_id": i["id"], "drive_url": i.get("webViewLink", "")}
        for n, i in enumerate(selected, 1)
    ]
    return {
        "generado": now.isoformat(),
        "estado": "PENDIENTE DE OK DE SANTIAGO (no publicado)",
        "torneo": batch["tournament"],
        "fecha": batch["fecha"],
        "texto": build_caption(batch),
        "fotos": photos,
        # Instagram admite carruseles de hasta 10 fotos; verificar el límite vigente antes de publicar.
        "grupos_sugeridos": [
            [p["n"] for p in photos[k:k + group_size]] for k in range(0, len(photos), group_size)
        ],
    }


def report_filename(batch: dict, now: datetime) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in f"{batch['tournament']}_{batch['fecha']}")
    return f"reports/{slug}_{now.strftime('%Y%m%d_%H%M')}.md"
