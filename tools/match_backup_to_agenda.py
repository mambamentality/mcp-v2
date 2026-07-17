# tools/match_backup_to_agenda.py — MatchBackupToAgenda (standalone; orchestrate_acta.py trae su propia copia interna)
import json
import logging
import re
from typing import List

import azure.functions as func

from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [ToolProperty("fileNames", "string", "Lista de nombres de archivo del directorio (JSON array).", isRequired=True)]
)

_PREFIX_RE = re.compile(r"^(\d+)(?:\.(\d+))?")
_EXCLUDE_KEYWORDS = ["convocatoria", "asistencia", "lista de asistencia", "acta maestra"]


def register_match_backup_to_agenda_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="MatchBackupToAgenda",
        description="Asocia cada archivo de respaldo con su punto del orden del día según el prefijo numérico del nombre.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def match_backup_to_agenda(context) -> str:
        try:
            args = get_arguments(context)
            file_names = args.get("fileNames")
            if isinstance(file_names, str):
                file_names = json.loads(file_names)
            if not isinstance(file_names, list):
                raise ValueError("'fileNames' debe ser una lista.")

            matches = []
            for name in file_names:
                if any(keyword in name.lower() for keyword in _EXCLUDE_KEYWORDS):
                    continue
                numero = extract_point_number(name)
                if numero:
                    matches.append({"fileName": name, "puntoNumero": numero})

            return json.dumps({"status": "ok", "matches": matches}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("MatchBackupToAgenda error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return match_backup_to_agenda


def extract_point_number(file_name: str) -> str:
    match = _PREFIX_RE.match(file_name.strip())
    if not match:
        return ""
    major = str(int(match.group(1)))
    minor = match.group(2)
    return f"{major}.{int(minor)}" if minor else major