"""Acceso de SOLO LECTURA a Google Drive con la cuenta de servicio (el "robot")."""
import io
import json
import os
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from . import config

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_MIME = "application/vnd.google-apps.folder"
FECHA_RE = re.compile(r"^\s*FECHA\s*(\d+)", re.IGNORECASE)

FILE_FIELDS = (
    "nextPageToken, files(id,name,mimeType,size,md5Checksum,createdTime,"
    "modifiedTime,webViewLink,owners(emailAddress))"
)


def client():
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_children(svc, folder_id: str) -> list[dict]:
    out, token = [], None
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields=FILE_FIELDS,
            pageSize=1000,
            pageToken=token,
        ).execute()
        out.extend(resp.get("files", []))
        token = resp.get("nextPageToken")
        if not token:
            return out


def find_batches(svc, only_folder_id: str = "") -> list[dict]:
    """Devuelve los lotes: una carpeta 'FECHA NN' dentro de cada torneo."""
    batches = []
    for tournament in list_children(svc, config.ROOT_FOLDER_ID):
        if tournament["mimeType"] != FOLDER_MIME:
            continue
        for child in list_children(svc, tournament["id"]):
            m = FECHA_RE.match(child["name"])
            if child["mimeType"] == FOLDER_MIME and m:
                if only_folder_id and child["id"] != only_folder_id:
                    continue
                batches.append({
                    "tournament": tournament["name"],
                    "fecha": f"FECHA {int(m.group(1)):02d}",
                    "folder_id": child["id"],
                })
    return batches


def list_images(svc, folder_id: str) -> list[dict]:
    files = list_children(svc, folder_id)
    return [f for f in files if f["mimeType"] in config.IMAGE_MIMES]


def download(svc, file_id: str) -> bytes:
    request = svc.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()
