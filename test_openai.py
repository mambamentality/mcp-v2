"""
Diagnóstico aislado de la conexión a Azure OpenAI.
Correr con: python test_openai.py
"""
import os, json

with open("local.settings.json", encoding="utf-8") as f:
    settings = json.load(f)
    for key, value in settings["Values"].items():
        os.environ[key] = value

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
key = os.environ.get("AZURE_OPENAI_KEY", "")
deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

print("=== Config actual (sanitizada) ===")
print(f"AZURE_OPENAI_ENDPOINT   = {endpoint!r}")
print(f"AZURE_OPENAI_DEPLOYMENT = {deployment!r}")
print(f"AZURE_OPENAI_API_VERSION= {api_version!r}")
print(f"AZURE_OPENAI_KEY        = {'*' * (len(key) - 4) + key[-4:] if key else '(vacío)'}")
print()

# Chequeos de formato comunes que causan 404
if endpoint and not endpoint.startswith("https://"):
    print("⚠️  El endpoint no empieza con https://")
if endpoint and endpoint.endswith("/"):
    print("ℹ️  El endpoint termina en '/' (el SDK lo maneja, pero verificalo)")
if "<" in endpoint or "<" in deployment or "<" in key:
    print("❌ Todavía hay placeholders sin reemplazar (contienen '<')")

print("\n=== Intentando listar deployments vía REST directo ===")
import requests
try:
    # Endpoint de management para listar deployments del recurso (requiere el mismo key)
    list_url = f"{endpoint.rstrip('/')}/openai/deployments?api-version={api_version}"
    resp = requests.get(list_url, headers={"api-key": key}, timeout=15)
    print(f"Status: {resp.status_code}")
    print(resp.text[:2000])
except Exception as exc:
    print(f"Error al listar: {exc}")

print("\n=== Intentando llamada real con AzureOpenAI SDK ===")
from openai import AzureOpenAI

try:
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
    )
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Responde solo con OK"}],
        max_tokens=5,
    )
    print("✅ Funciona. Respuesta:", response.choices[0].message.content)
except Exception as exc:
    print(f"❌ Falló: {type(exc).__name__}: {exc}")