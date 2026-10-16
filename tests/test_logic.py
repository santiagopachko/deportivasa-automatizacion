from datetime import datetime, timedelta, timezone

from deportivasa import selection, stability

NOW = datetime(2026, 10, 15, 23, 0, tzinfo=timezone.utc)


def files_uploaded(minutes_ago_list):
    return [
        {"id": f"f{i}", "createdTime": (NOW - timedelta(minutes=m)).isoformat().replace("+00:00", "Z")}
        for i, m in enumerate(minutes_ago_list)
    ]


def test_no_estable_si_llegaron_fotos_recientes():
    assert not stability.is_stable(files_uploaded([500, 30]), NOW, 60)


def test_estable_si_pasaron_60_minutos():
    assert stability.is_stable(files_uploaded([500, 61]), NOW, 60)


def test_carpeta_vacia_no_es_estable():
    assert not stability.is_stable([], NOW, 60)


def test_huella_cambia_si_se_agrega_una_foto():
    a = files_uploaded([100, 90])
    b = files_uploaded([100, 90, 80])
    assert stability.fingerprint(a) != stability.fingerprint(b)
    assert stability.fingerprint(a) == stability.fingerprint(list(reversed(a)))


def foto(name, **over):
    base = {
        "id": name, "name": name, "valid": True, "width": 6000, "height": 4000,
        "short_side": 4000, "sharpness": 200.0,
        "analysis": {"contiene_documento": False, "datos_personales_legibles": False,
                     "calidad": 8, "accion": "gol", "colores_camisetas": ["rojo"],
                     "publicable": True, "confianza": 0.9, "motivo": "ok"},
    }
    base.update(over)
    return base


def test_excluye_documentos_y_datos_personales():
    doc = foto("a.jpg")
    doc["analysis"] = {**doc["analysis"], "contiene_documento": True}
    dni = foto("b.jpg")
    dni["analysis"] = {**dni["analysis"], "datos_personales_legibles": True}
    assert any("documento" in r for r in selection.exclusion_reasons(doc))
    assert any("personales" in r for r in selection.exclusion_reasons(dni))


def test_no_baja_el_umbral_de_confianza():
    dudosa = foto("c.jpg")
    dudosa["analysis"] = {**dudosa["analysis"], "confianza": 0.5}
    assert selection.exclusion_reasons(dudosa)


def test_excluye_baja_resolucion_borrosa_duplicada_y_danada():
    assert selection.exclusion_reasons(foto("d.jpg", short_side=600, width=800, height=600))
    assert selection.exclusion_reasons(foto("e.jpg", sharpness=5.0))
    assert selection.exclusion_reasons(foto("f.jpg", duplicate_of="x.jpg"))
    assert selection.exclusion_reasons({"id": "g", "name": "g.jpg", "valid": False, "error": "roto"})
    assert selection.exclusion_reasons(foto("h.jpg", incomplete=True))


def test_sin_analisis_de_ia_se_excluye():
    sin_ia = foto("i.jpg", analysis=None, analysis_error="timeout")
    assert any("fallido" in r for r in selection.exclusion_reasons(sin_ia))


def test_seleccion_respeta_cantidad_y_variedad():
    acciones = ["gol", "atajada", "disputa", "festejo"]
    items = []
    for n in range(40):
        f = foto(f"DSC_{1000 + n * 10}.jpg")
        f["analysis"] = {**f["analysis"], "accion": acciones[n % 4],
                         "colores_camisetas": ["rojo" if n % 2 else "azul"]}
        items.append(f)
    elegidas = selection.select(items, 20)
    assert len(elegidas) == 20
    assert len({e["analysis"]["accion"] for e in elegidas}) == 4


def test_seleccion_evita_rafagas_cuando_hay_alternativas():
    rafaga = [foto(f"DSC_{2000 + n}.jpg") for n in range(5)]
    otras = [foto(f"DSC_{5000 + n * 50}.jpg") for n in range(5)]
    elegidas = selection.select(rafaga + otras, 5)
    en_rafaga = [e for e in elegidas if e["name"].startswith("DSC_20")]
    assert len(en_rafaga) <= 2


def test_seleccion_no_inventa_fotos_si_hay_pocas_aptas():
    items = [foto("ok.jpg"), foto("mala.jpg", sharpness=1.0)]
    assert [e["name"] for e in selection.select(items, 20)] == ["ok.jpg"]
