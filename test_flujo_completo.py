"""
Prueba end-to-end del flujo completo de negocio:

  ProcessGestionDirectory -> SetAttendanceModality -> ApproveActa -> FinalizeActa

Corre cada paso, mide tiempo, y al final imprime un resumen claro de qué
pasó y qué falló. Si un paso falla, el script se detiene ahí (no tiene
sentido seguir con un actaId que no llegó al estado esperado).

AJUSTÁ estas variables antes de correr:
"""
import os, json, time, sys

# ============ CONFIGURACIÓN — AJUSTAR ============
GESTION = "2024"
DIRECTORIO = "23-04-2024"
NUMERO_ACTA = None  # None = se sugiere automáticamente
# Modalidad por defecto para TODOS los asistentes detectados (para poder
# correr el flujo sin intervención manual). Ajustá a mano si necesitás
# modalidades distintas por persona antes de aprobar de verdad.
MODALIDAD_DEFAULT = "presencial"
# ===================================================

with open("local.settings.json", encoding="utf-8") as f:
    settings = json.load(f)
    for key, value in settings["Values"].items():
        os.environ[key] = value

import azure.functions as func
from tools.orchestrate_acta import register_process_gestion_directory_tool
from tools.set_attendance_modality import register_set_attendance_modality_tool
from tools.approve_acta import register_approve_acta_tool
from tools.finalize_acta import register_finalize_acta_tool
from tools.acta_draft_store import ActaDraftStore

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
process_gestion = register_process_gestion_directory_tool(app)
set_modalidad = register_set_attendance_modality_tool(app)
approve_acta = register_approve_acta_tool(app)
finalize_acta = register_finalize_acta_tool(app)

store = ActaDraftStore()

# Resumen de pasos: (nombre, ok/fail, segundos, detalle)
steps_summary = []


def run_step(name: str, fn):
    """Ejecuta un paso, mide tiempo, imprime resultado, registra en el resumen.
    Si falla, imprime el error y corta la ejecución del script."""
    print(f"\n{'=' * 60}")
    print(f"PASO: {name}")
    print("=" * 60)
    start = time.time()
    try:
        result = fn()
        elapsed = time.time() - start
        print(f"\n✅ OK ({elapsed:.1f}s)")
        steps_summary.append((name, "OK", elapsed, ""))
        return result
    except Exception as exc:
        elapsed = time.time() - start
        print(f"\n❌ FALLÓ ({elapsed:.1f}s): {type(exc).__name__}: {exc}")
        steps_summary.append((name, "FAIL", elapsed, str(exc)))
        print_summary()
        sys.exit(1)


def call_tool(tool_fn, arguments: dict) -> dict:
    raw = tool_fn({"arguments": arguments})
    result = json.loads(raw)
    print(json.dumps(result, ensure_ascii=False, indent=2)[:3000])
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Error desconocido"))
    return result


def print_summary():
    print(f"\n{'=' * 60}")
    print("RESUMEN")
    print("=" * 60)
    for name, status, elapsed, detail in steps_summary:
        icon = "✅" if status == "OK" else "❌"
        print(f"{icon} {name:35s} {elapsed:6.1f}s  {status}")
        if detail:
            print(f"     └─ {detail}")


# ---------- PASO 1: ProcessGestionDirectory ----------
def step_process():
    args = {"gestion": GESTION, "directorio": DIRECTORIO}
    if NUMERO_ACTA:
        args["numeroActa"] = NUMERO_ACTA
    return call_tool(process_gestion, args)


result1 = run_step("1. ProcessGestionDirectory", step_process)
acta_id = result1["actaId"]
print(f"\n>>> actaId = {acta_id}")

# Inspección del acta guardada (fuera del tool, directo del store, para
# ver el detalle completo sin el truncado a 3000 chars del print de arriba)
acta = store.get_acta(acta_id)
asistentes = acta.get("asistentes", [])
print(f"\n>>> Asistentes detectados ({len(asistentes)}):")
for a in asistentes:
    print(f"    - {a.get('nombre')!r} (asistió: {a.get('asistio')})")

print(f"\n>>> Puntos del orden del día ({len(acta.get('ordenDelDia', []))}):")
def _resumen_puntos(points, indent=0):
    for p in points:
        print(f"{'  ' * indent}  {p.get('numero')} - {p.get('titulo', '')[:60]} "
              f"[{p.get('maestroEstado')}]")
        _resumen_puntos(p.get("subpuntos", []), indent + 1)
_resumen_puntos(acta.get("ordenDelDia", []))


# ---------- PASO 2: SetAttendanceModality ----------
def step_modalidad():
    # Asigna MODALIDAD_DEFAULT a todos los asistentes detectados.
    modalidad_map = {a["nombre"]: MODALIDAD_DEFAULT for a in asistentes if a.get("nombre")}
    if not modalidad_map:
        raise RuntimeError(
            "No hay asistentes para asignar modalidad — revisar ExtractAttendance/"
            "ProcessGestionDirectory, algo falló en detectar nombres."
        )
    print(f"Asignando modalidad {MODALIDAD_DEFAULT!r} a {len(modalidad_map)} personas.")
    return call_tool(set_modalidad, {"actaId": acta_id, "modalidadPorPersona": modalidad_map})


run_step("2. SetAttendanceModality", step_modalidad)


# ---------- PASO 3: ApproveActa ----------
def step_approve():
    return call_tool(approve_acta, {"actaId": acta_id})


run_step("3. ApproveActa", step_approve)


# ---------- PASO 4: FinalizeActa ----------
def step_finalize():
    return call_tool(finalize_acta, {"actaId": acta_id})


result4 = run_step("4. FinalizeActa", step_finalize)

# Guardar copia local del docx final para inspección visual rápida
if result4.get("fileBase64"):
    import base64
    out_path = f"_test_output_{result4.get('fileName', 'acta.docx')}"
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(result4["fileBase64"]))
    print(f"\n>>> Copia local guardada en: {out_path}")
    print(f">>> Subido a SharePoint en: {result4.get('webUrl')}")


print_summary()
print(f"\n>>> actaId usado en esta corrida: {acta_id}")
print(">>> (guardalo si querés re-probar pasos individuales sobre la misma acta)")