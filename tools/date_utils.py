# tools/date_utils.py — nuevo archivo
"""Normaliza fechas en distintos formatos (texto largo en español, fechas
de Excel, datetime) a un formato comparable YYYY-MM-DD."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_TEXT_DATE_RE = re.compile(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", re.IGNORECASE)


def normalize_date(value) -> Optional[str]:
    """Acepta datetime, string tipo '23-abr-24', o texto largo en español
    ('martes 23 de abril de 2024'). Devuelve 'YYYY-MM-DD' o None si no se
    pudo interpretar."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    text = str(value).strip()

    match = _TEXT_DATE_RE.search(text)
    if match:
        day, mes_texto, year = match.groups()
        mes_num = _MESES.get(mes_texto.lower())
        if mes_num:
            return f"{int(year):04d}-{mes_num:02d}-{int(day):02d}"

    for fmt in ("%d-%b-%y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None