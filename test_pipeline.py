"""
Prueba end-to-end de ProcessGestionDirectory contra SharePoint real.
Correr con: python test_pipeline.py
"""
import os, json

with open("local.settings.json", encoding="utf-8") as f:
    settings = json.load(f)
    for key, value in settings["Values"].items():
        os.environ[key] = value

import azure.functions as func
from tools.orchestrate_acta import register_process_gestion_directory_tool

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
process_gestion = register_process_gestion_directory_tool(app)

print("=== ProcessGestionDirectory ===")
raw = process_gestion({
    "arguments": {
        "gestion": "2024",
        "directorio": "23-04-2024",
    }
})
result = json.loads(raw)
print(json.dumps(result, ensure_ascii=False, indent=2))

if result.get("status") == "error":
    print("\n!!! FALLÓ. Revisar el traceback completo en los logs de Python (logger.exception) !!!")
else:
    acta_id = result["actaId"]
    print(f"\nOK. actaId = {acta_id}")
    print("Guardado en: %TEMP%/mcp_data/acta_drafts.json (o $MCP_DATA_DIR si está seteada)")

    # Inspeccionar el acta guardada para revisar los nombres de asistentes
    # (los vamos a necesitar para el siguiente paso: SetAttendanceModality)
    from tools.acta_draft_store import ActaDraftStore
    store = ActaDraftStore()
    acta = store.get_acta(acta_id)
    print("\n=== Asistentes detectados ===")
    for a in acta.get("asistentes", []):
        print(f"  - {a.get('nombre')!r} (asistió: {a.get('asistio')})")

    print("\n=== Primeros 2 puntos del orden del día (con estado de match a Maestra) ===")
    for p in acta.get("ordenDelDia", [])[:2]:
        print(f"  {p.get('numero')} - {p.get('titulo')}")
        print(f"    maestroEstado: {p.get('maestroEstado')}, tipo: {p.get('tipo')}")
        print(f"    narrativa (primeros 200 chars): {(p.get('narrativa') or '')[:200]}")
        print(f"    determinacion (primeros 200 chars): {(p.get('determinacion') or '')[:200]}")