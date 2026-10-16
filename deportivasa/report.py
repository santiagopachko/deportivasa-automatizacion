"""Informe del lote: archivo Markdown en el repositorio y mail de resumen."""
import os
import smtplib
from collections import Counter
from datetime import datetime
from email.message import EmailMessage
from html import escape


def build_markdown(batch: dict, items: list[dict], selected: list[dict], reasons: dict, usage: dict) -> str:
    excluded = [i for i in items if reasons[i["id"]]]
    counts = Counter(r.split(" (")[0] for i in excluded for r in reasons[i["id"]])
    lines = [
        f"# {batch['tournament']} — {batch['fecha']} (MODO PRUEBA, no se publicó nada)",
        "",
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


def build_html(batch: dict, items: list[dict], selected: list[dict], reasons: dict, usage: dict) -> str:
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


def report_filename(batch: dict, now: datetime) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in f"{batch['tournament']}_{batch['fecha']}")
    return f"reports/{slug}_{now.strftime('%Y%m%d_%H%M')}.md"
