# Servidor MCP — Actas Bancarias
**Empresa S.A. | Uso Interno y Confidencial**

Servidor MCP construido sobre Azure Functions Python. Expone herramientas MCP para administrar el flujo completo de captura de actas, validación, generación de borrador, edición, aprobación y conversión final a Word.

---

## Tools disponibles

| Tool | Descripción |
|---|---|
| `ActaWizard` | Gestiona la creación de sesiones, captura de datos, guardado de respuestas y preguntas siguientes. |
| `ValidateActa` | Valida que los campos obligatorios del acta estén completos. |
| `GenerateDraft` | Genera un borrador de acta en Markdown usando los datos capturados. |
| `UpdateDraft` | Permite modificar el borrador antes de su aprobación. |
| `ApproveDraft` | Registra la aprobación formal del borrador. |
| `GenerateDocx` | Convierte el borrador aprobado en un documento Word (devuelto en base64). |

### Flujo de negocio

ActaWizard → ValidateActa → GenerateDraft → Mostrar borrador → UpdateDraft (0 o más veces) → ApproveDraft → GenerateDocx

---

## Requisitos previos

- Python 3.10+ (recomendado 3.12)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (emulador de Storage — requerido incluso en local, el extension MCP lo usa para el transporte SSE)
- `azure-functions>=1.24.0` (el `mcp_tool_trigger` no funciona con versiones anteriores)

---

## 1. Instalar dependencias

```bash
python3 -m venv .venv
. .venv/bin/activate       # en Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Correr los tests (sin necesidad de levantar el servidor)

Los tests en `tests/test_tools.py` llaman directamente a la lógica de cada tool,
sin pasar por el runtime de Azure Functions ni por Azurite. Son la forma más
rápida de verificar que la lógica de negocio funciona:

```bash
pytest -v
```

Deberían pasar 5 tests que cubren: creación de sesión, flujo completo hasta
generar el DOCX, validación con campos faltantes, y que un borrador aprobado
no se puede editar.

## 3. Levantar el servidor MCP real

```bash
# En otra terminal, arrancar el emulador de storage:
azurite --silent --location .azurite --debug .azurite/debug.log
# o, en VS Code: Ctrl+Shift+P -> "Azurite: Start"

func start
```

El servidor MCP expone el webhook en:

```
http://localhost:7071/runtime/webhooks/mcp
```

## 4. Probar los tools end-to-end

Dos formas:

**a) MCP Inspector (recomendado, habla el protocolo real):**
```bash
npx @modelcontextprotocol/inspector
```
Conectar a `http://localhost:7071/runtime/webhooks/mcp/sse`, listar tools e
invocarlas una por una viendo el JSON de respuesta.

**b) Postman:** importar `tests/Actas_MCP_Postman.json` y correr los requests
en orden (01 a 07). Los primeros dos requests guardan automáticamente
`session_id` y `draft_id` como variables de colección para los siguientes.

---

## Notas importantes

- `local.settings.json` está en `.gitignore`. No subas credenciales al repositorio.
- El estado (sesiones, borradores) se guarda en `.data/*.json` junto al proyecto.
  Esto es suficiente para desarrollo local, pero **no es apto para producción**:
  en Azure Functions el filesystem local no es persistente ni se comparte entre
  instancias. Antes de desplegar con más de una instancia, reemplazar
  `tools/storage.py` por Azure Table Storage, Cosmos DB o Blob Storage.
- `host.json` tiene `system.webhookAuthorizationLevel: "Anonymous"` para
  facilitar las pruebas locales. **Antes de desplegar a Azure**, cambiarlo a
  `"Function"` o `"System"` para requerir la key `mcp_extension`.
- `UpdateDraft` interpreta instrucciones en español con reglas simples
  (reemplazar/eliminar/agregar); instrucciones ambiguas se agregan al final
  del borrador en vez de aplicarse quirúrgicamente. Es una limitación conocida,
  no un bug.

---

## Tips rápidos

- `ActaWizard` devuelve `sessionId`, `status`, `nextField` y `question`.
- `ValidateActa` devuelve `complete` y `missingFields`.
- `GenerateDraft` crea el borrador con `draftId` y `draftMarkdown`.
- `UpdateDraft` no puede editar un borrador aprobado.
- `GenerateDocx` solo funciona si el borrador está aprobado, y devuelve el
  archivo como `fileBase64` (decodificar para obtener el `.docx`).
