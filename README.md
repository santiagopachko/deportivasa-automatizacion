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
6. Guarda un informe en `reports/` y manda el resumen por mail.

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
