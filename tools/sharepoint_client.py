# tools/sharepoint_client.py
"""Cliente delgado sobre Microsoft Graph para leer/escribir en SharePoint.
Usa client credentials flow (permisos de aplicación)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import msal
import requests

from .config import get_env

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_token_cache: Dict[str, Any] = {}


def _get_token() -> str:
    cached = _token_cache.get("access_token")
    if cached:
        return cached

    tenant_id = get_env("SP_TENANT_ID")
    client_id = get_env("SP_CLIENT_ID")
    client_secret = get_env("SP_CLIENT_SECRET")

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"No se pudo obtener token de Graph: {result.get('error_description')}")

    _token_cache["access_token"] = result["access_token"]
    return result["access_token"]


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {_get_token()}"}


# tools/sharepoint_client.py — reemplazar la función list_children completa

def list_children(folder_path: str = "") -> List[Dict[str, Any]]:
    """Lista archivos/carpetas de una ruta relativa a la raíz del drive del sitio.
    Si folder_path está vacío, lista la raíz del drive."""
    site_id = get_env("SP_SITE_ID")
    clean_path = folder_path.strip("/")

    if clean_path:
        url = f"{GRAPH_BASE}/sites/{site_id}/drive/root:/{clean_path}:/children"
    else:
        url = f"{GRAPH_BASE}/sites/{site_id}/drive/root/children"

    items = []
    while url:
        resp = requests.get(url, headers=_headers(), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("value", []))
        url = payload.get("@odata.nextLink")

    return [
        {
            "id": item["id"],
            "name": item["name"],
            "path": f"{clean_path}/{item['name']}" if clean_path else item["name"],
            "isFolder": "folder" in item,
            "size": item.get("size"),
            "webUrl": item.get("webUrl"),
        }
        for item in items
    ]


def download_file(file_path: str) -> bytes:
    site_id = get_env("SP_SITE_ID")
    clean_path = file_path.strip("/")
    url = f"{GRAPH_BASE}/sites/{site_id}/drive/root:/{clean_path}:/content"
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.content


def upload_file(folder_path: str, file_name: str, content: bytes) -> Dict[str, Any]:
    site_id = get_env("SP_SITE_ID")
    clean_folder = folder_path.strip("/")
    url = f"{GRAPH_BASE}/sites/{site_id}/drive/root:/{clean_folder}/{file_name}:/content"

    headers = _headers()
    headers["Content-Type"] = "application/octet-stream"

    resp = requests.put(url, headers=headers, data=content, timeout=60)
    resp.raise_for_status()
    return resp.json()