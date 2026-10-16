"""Configuración de la Fase 1. Todo se puede cambiar con variables de entorno."""
import os

# Carpeta "03 — Fotografías y audiovisuales" (fuente única de fotos).
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID", "123AGsQC19fSRsu9kpb1FpPCkUU5eFw3G")

# Una carga se considera completa si el último archivo subido tiene al menos
# estos minutos de antigüedad (se mide con la fecha de subida a Drive).
STABLE_MINUTES = int(os.environ.get("STABLE_MINUTES", "60"))

# Cantidad de fotos a elegir por lote.
SELECT_COUNT = int(os.environ.get("SELECT_COUNT", "20"))

# Controles técnicos. MIN_SHARPNESS es un valor inicial: hay que calibrarlo
# con fotos reales mirando los valores que aparecen en el informe.
MIN_SHORT_SIDE = int(os.environ.get("MIN_SHORT_SIDE", "1000"))
MIN_SHARPNESS = float(os.environ.get("MIN_SHARPNESS", "40"))

# Confianza mínima de la IA para considerar publicable una foto.
# Si no se alcanza, la foto se EXCLUYE. No bajar este valor para "forzar" resultados.
MIN_CONFIDENCE = float(os.environ.get("MIN_CONFIDENCE", "0.7"))

# Modelo usado para revisar cada foto.
MODEL = os.environ.get("MODEL_TRIAGE", "claude-haiku-5-5")

# Lotes que se procesan como máximo por ejecución (controla tiempo y costo).
MAX_BATCHES_PER_RUN = int(os.environ.get("MAX_BATCHES_PER_RUN", "1"))

# Modo SIN IA: se descarta la foto si más de esta proporción parece "papel" (planilla/documento).
# Es una detección simple y aproximada; hay que calibrarla con fotos reales.
PAPER_RATIO_MAX = float(os.environ.get("PAPER_RATIO_MAX", "0.45"))

IMAGE_MIMES ={"image/jpeg", "image/png"}
