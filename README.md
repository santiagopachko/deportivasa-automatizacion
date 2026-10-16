# DEPORTIVASA — Automatización de fotos (Fase 1, modo prueba)

Lee las carpetas de fotos de Drive, espera a que cada carga termine, descarta fotos
inservibles o con datos personales, elige las mejores y envía un resumen por mail.

**Esta fase NO publica en redes y NO borra nada.**

## Qué hace

1. Recorre `03 — Fotografías y audiovisuales` → torneo → `FECHA NN` (solo lectura).
2. Considera completa una carga cuando pasó 1 hora sin archivos nuevos.
3. Controla: imagen válida y completa, no duplicada, resolución y nitidez mínimas.
4. Revisa cada foto con IA: planillas/DNI/datos personales, calidad, tipo de jugada.
5. Elige las 20 mejores con variedad de jugadas y camisetas, evitando ráfagas.
6. Guarda en `reports/`: el informe, una **hoja de contactos** numerada para revisar de un vistazo
   y una **lista para publicar** con el texto armado, pendiente del OK.
7. Sin clave de IA funciona igual (gratis): elige por nitidez y reparto, y detecta planillas con un
   método simple. En ese modo el informe avisa que hay que revisar a mano.

## Flujo de aprobación

El programa prepara todo; **la publicación solo se hace con el OK explícito de Santiago**,
que se da en el chat con Claude ("ok, publicá" / "sacá la 7 y la 12").

## Cómo se usa

Pestaña **Actions** → **Fase 1 - Revisar fotos (modo prueba)** → **Run workflow**.

- `listing`: solo mira Drive y muestra qué lotes hay. Sin costo de IA.
- `full`: procesa un lote completo (consume API de Anthropic).

Guía de claves: [docs/CONFIGURACION.md](docs/CONFIGURACION.md).

## Reglas del proyecto

- Los DNI y planillas de jugadores nunca se guardan en este repositorio.
- Las claves nunca van en el código: se guardan en los *Secrets* del repositorio.
- No se baja el umbral de confianza para forzar resultados: ante la duda, se excluye.

## Estado

Escrito y probado solo con datos sintéticos (lógica de estabilidad, exclusión y
selección; controles de imagen). **Todavía no se ejecutó contra el Drive real ni con
la IA real.** Los umbrales de nitidez hay que calibrarlos con fotos reales.
