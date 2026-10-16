# Configuración de claves (Secrets)

Todas las claves se cargan en GitHub, **nunca en el chat ni en el código**:
repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

## Paso 1 — Para el modo `listing` (sin costo)

| Nombre del secret | Qué es |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Contenido completo del archivo de clave del robot `deportivasa-bot` |

Cómo obtener el archivo:
1. https://console.cloud.google.com/iam-admin/serviceaccounts (proyecto DEPORTIVASA)
2. Entrar al robot `deportivasa-bot` → pestaña **Claves** → **Agregar clave** → **Crear clave nueva** → **JSON**.
3. Se descarga un archivo `.json`. Abrilo con el Bloc de notas, copiá TODO el texto y pegalo como valor del secret.
4. Después de pegarlo, borrá el archivo descargado de tu computadora.

Si Google no deja crear la clave, puede haber una política de la organización que lo bloquea; avisar.

## Paso 2 — Para el modo `full`

| Nombre del secret | Qué es |
|---|---|
| `ANTHROPIC_API_KEY` | Clave de API de console.anthropic.com (requiere saldo cargado) |
| `GMAIL_USER` | Mail desde el que se envían los resúmenes (puede ser santiagopachko@gmail.com) |
| `GMAIL_APP_PASSWORD` | "Contraseña de aplicación" de Google (requiere verificación en dos pasos) |
| `MAIL_TO` | Mail que recibe los resúmenes |

Si faltan los datos de Gmail, el programa igual funciona y guarda el informe en `reports/`.

## Ajustes (opcionales)

Variables de entorno en el workflow: `STABLE_MINUTES`, `SELECT_COUNT`, `MIN_SHARPNESS`,
`MIN_SHORT_SIDE`, `MIN_CONFIDENCE`, `MODEL_TRIAGE`, `MAX_BATCHES_PER_RUN`.
