"""
Test aislado de extracción + parseo de una Convocatoria real (posiblemente
escaneada), para confirmar que:
  1) _extract_text ya NO se corta en 5 páginas (max_pages=None aplicado).
  2) fecha/hora/lugar/orden del día/roles se parsean razonablemente bien
     sobre texto que puede venir con ruido de OCR.

Ajustá FILE_PATH abajo. Correr con: python test_convocatoria.py
"""
import os, json, time

with open("local.settings.json", encoding="utf-8") as f:
    settings = json.load(f)
    for key, value in settings["Values"].items():
        os.environ[key] = value

FILE_PATH = "Actas/Insumos/2024/23-04-2024/00. 2024.04.23 Convocatoria Directorio.pdf"  # <-- AJUSTAR

from tools import sharepoint_client
from tools.extract_convocatoria import (
    _extract_text, _first_match, _detect_modalidad,
    _parse_orden_del_dia, _parse_roles, _DATE_RE, _TIME_RE, _PLACE_RE,
)

print(f"Descargando: {FILE_PATH}")
content = sharepoint_client.download_file(FILE_PATH)

# Chequeo rápido de cuántas páginas tiene el PDF real
import fitz
doc = fitz.open(stream=content, filetype="pdf")
print(f"El PDF tiene {doc.page_count} páginas.")
doc.close()

print("\nExtrayendo texto (esto puede tardar si es escaneado)...")
start = time.time()
text = _extract_text(content)
elapsed = time.time() - start
print(f"Terminó en {elapsed:.1f}s. Caracteres extraídos: {len(text)}")

print("\n=== FECHA/HORA/LUGAR/MODALIDAD ===")
print("Fecha:", _first_match(_DATE_RE, text))
print("Hora:", _first_match(_TIME_RE, text))
print("Lugar:", _first_match(_PLACE_RE, text))
print("Modalidad:", _detect_modalidad(text))

print("\n=== ORDEN DEL DÍA ===")
orden = _parse_orden_del_dia(text)
print(f"Puntos top-level encontrados: {len(orden)}")
print(json.dumps(orden, ensure_ascii=False, indent=2))

print("\n=== ROLES ===")
roles = _parse_roles(text)
print(json.dumps(roles, ensure_ascii=False, indent=2))
total_nombres = sum(len(v) for v in roles.values())
print(f"\nTotal de nombres detectados en roles: {total_nombres}")
if total_nombres == 0:
    print("⚠️  No se detectó ningún nombre — revisar _parse_roles contra el texto real (ver abajo).")

print("\n=== Primeros 1000 caracteres del texto extraído (para inspección manual) ===")
print(text[:1000])