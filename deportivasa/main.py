"""Fase 1 — modo prueba. NO publica en redes y NO borra nada.

Modos:
  listing  Solo mira Drive y muestra qué lotes hay y si están estables. Sin costo.
  full     Descarga, revisa con IA, elige las mejores y envía el resumen.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config, contactsheet, drive, report, selection, stability

STATE_FILE = Path("state/state.json")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"batches": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def summary(text: str) -> None:
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def run_listing(svc, only_folder: str) -> None:
    now = datetime.now(timezone.utc)
    state = load_state()
    summary("## Lotes encontrados en Drive (modo listado, no se procesó nada)\n")
    summary("| Torneo | Fecha | Fotos | Minutos desde la última subida | ¿Estable? | ¿Ya procesado? |")
    summary("|---|---|---:|---:|---|---|")
    for b in drive.find_batches(svc, only_folder):
        files = drive.list_images(svc, b["folder_id"])
        mins = stability.minutes_since_last_upload(files, now)
        stable = stability.is_stable(files, now, config.STABLE_MINUTES)
        done = state["batches"].get(b["folder_id"], {}).get("fingerprint") == stability.fingerprint(files) if files else False
        summary(
            f"| {b['tournament']} | {b['fecha']} | {len(files)} | "
            f"{'-' if mins is None else round(mins)} | {'sí' if stable else 'no'} | {'sí' if done else 'no'} |"
        )


def process_batch(svc, batch: dict, files: list[dict]) -> dict:
    from . import imaging

    use_ai = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if use_ai:
        from . import analyze
    seen_md5: dict[str, str] = {}
    items, usage = [], {"input": 0, "output": 0}
    for n, f in enumerate(sorted(files, key=lambda x: x["name"]), 1):
        item = {"id": f["id"], "name": f["name"], "webViewLink": f.get("webViewLink", "")}
        md5 = f.get("md5Checksum")
        if md5 and md5 in seen_md5:
            item.update(valid=True, duplicate_of=seen_md5[md5], width=0, height=0, short_side=0, sharpness=0)
            items.append(item)
            continue
        if md5:
            seen_md5[md5] = f["name"]

        data = drive.download(svc, f["id"])
        if f.get("size") and int(f["size"]) != len(data):
            item.update(valid=False, incomplete=True)
            items.append(item)
            continue
        info = imaging.inspect(data)
        preview = info.pop("preview_jpeg", None)
        item.update(info)
        item["preview"] = preview  # se usa para la hoja de contactos; no se guarda en el informe
        if not use_ai:
            # Modo SIN IA: no hay juicio sobre el contenido; solo controles técnicos.
            item["no_ai"] = True
            item["analysis"] = {
                "contiene_documento": False, "datos_personales_legibles": False,
                "calidad": 5, "accion": "otro", "colores_camisetas": [],
                "publicable": True, "confianza": 1.0, "motivo": "sin revisión de IA",
            }
        elif item["valid"] and not selection.technical_reasons(item) and preview:
            result, used, err = analyze.analyze(preview)
            item["analysis"], item["analysis_error"] = result, err
            usage["input"] += used["input"]
            usage["output"] += used["output"]
        items.append(item)
        if n % 10 == 0:
            print(f"  procesadas {n}/{len(files)}")

    reasons = {i["id"]: selection.exclusion_reasons(i) for i in items}
    chooser = selection.select if use_ai else selection.select_spread
    selected = chooser(items, config.SELECT_COUNT)
    return {"items": items, "selected": selected, "reasons": reasons, "usage": usage, "use_ai": use_ai}


def run_full(svc, only_folder: str) -> int:
    now = datetime.now(timezone.utc)
    state = load_state()
    processed = 0
    for b in drive.find_batches(svc, only_folder):
        if processed >= config.MAX_BATCHES_PER_RUN:
            break
        files = drive.list_images(svc, b["folder_id"])
        if not files:
            continue
        fp = stability.fingerprint(files)
        if state["batches"].get(b["folder_id"], {}).get("fingerprint") == fp:
            continue  # ya procesado, sin cambios
        if not stability.is_stable(files, now, config.STABLE_MINUTES):
            print(f"{b['tournament']} {b['fecha']}: carga en curso, se espera.")
            continue

        print(f"Procesando {b['tournament']} {b['fecha']} ({len(files)} fotos)...")
        res = process_batch(svc, b, files)
        md = report.build_markdown(b, res["items"], res["selected"], res["reasons"], res["usage"], res["use_ai"])
        out = Path(report.report_filename(b, now))
        out.parent.mkdir(parents=True, exist_ok=True)

        sheet_path = out.with_name(out.stem + "_contactos.jpg")
        publish_path = out.with_name(out.stem + "_publicar.json")
        selected_with_preview = [i for i in res["selected"] if i.get("preview")]
        if selected_with_preview:
            sheet_path.write_bytes(contactsheet.build(selected_with_preview))
        publish_path.write_text(
            json.dumps(report.build_publish_list(b, res["selected"], now), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # Métricas de TODAS las fotos, para calibrar los umbrales con datos reales.
        metrics_path = out.with_name(out.stem + "_metricas.csv")
        chosen = {i["id"] for i in res["selected"]}
        with metrics_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["archivo", "ancho", "alto", "nitidez", "papel", "elegida", "motivos_exclusion"])
            for i in sorted(res["items"], key=lambda x: x["name"]):
                writer.writerow([
                    i["name"], i.get("width", ""), i.get("height", ""), i.get("sharpness", ""),
                    i.get("paper_ratio", ""), "sí" if i["id"] in chosen else "no",
                    "; ".join(res["reasons"][i["id"]]),
                ])
        md += (
            "\n## Para revisar y dar el OK\n"
            f"- Hoja de contactos (fotos numeradas como en la lista de arriba): `{sheet_path.name}`\n"
            f"- Lista y texto listos para publicar, pendiente del OK: `{publish_path.name}`\n"
        )
        out.write_text(md, encoding="utf-8")

        html = report.build_html(b, res["items"], res["selected"], res["reasons"], res["usage"], res["use_ai"])
        mail_status = report.send_mail(f"DEPORTIVASA — Resumen (prueba): {b['tournament']} {b['fecha']}", html)
        summary(f"**{b['tournament']} {b['fecha']}**: {len(res['selected'])} elegidas de {len(files)}. {mail_status}.")

        state["batches"][b["folder_id"]] = {
            "fingerprint": fp,
            "processed_at": now.isoformat(),
            "selected": [i["name"] for i in res["selected"]],
        }
        save_state(state)
        processed += 1
    if processed == 0:
        summary("No había lotes nuevos y estables para procesar.")
    return 0


def run_demo(svc) -> int:
    """Genera historias de prueba con las fotos ORIGINALES (alta calidad). No publica nada."""
    from . import stories

    ids = [x.strip() for x in os.environ.get("DEMO_FILE_IDS", "").split(",") if x.strip()] or [
        "1TKjX6gEK1hyJ0e5UjSjwKkHIZfo79Kws",  # 05 DSC_0981 vertical
        "10VXPiMwEJUQF0RVl_3BOziclutDOstts",  # 19 DSC_1100 vertical
        "1X8HbsgbFxMpiVnofXS07DNs0tgsiGcec",  # 13 DSC_1045 horizontal (recorte central)
    ]
    out_dir = Path("reports/demo")
    out_dir.mkdir(parents=True, exist_ok=True)
    for n, fid in enumerate(ids, 1):
        data = drive.download(svc, fid)
        for final in (False, True):
            name = f"historia_{n}_{'final_link_en_bio' if final else 'normal'}.jpg"
            (out_dir / name).write_bytes(stories.build_story(data, "FECHA 04", "Sábados F8 · Lugano", final))
            print("generada", name)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["listing", "full", "demo"], default="listing")
    parser.add_argument("--folder-id", default="")
    args = parser.parse_args()
    svc = drive.client()
    if args.mode == "demo":
        return run_demo(svc)
    if args.mode == "listing":
        run_listing(svc, args.folder_id)
        return 0
    return run_full(svc, args.folder_id)


if __name__ == "__main__":
    sys.exit(main())
