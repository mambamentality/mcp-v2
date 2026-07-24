# create_catalog.py — correr una sola vez
import os, json
from openpyxl import Workbook

with open("local.settings.json", encoding="utf-8") as f:
    settings = json.load(f)
    for key, value in settings["Values"].items():
        os.environ[key] = value

from tools import sharepoint_client

wb = Workbook()
sheet = wb.active
sheet.title = "Catalogo"
sheet.append(["nombreCompleto", "alias", "rol", "genero", "cargo"])

data = [
    ("Ximena Behoteguy", "Ximena Behoteguy Terrazas", "Presidencia", "F", ""),
    ("Andrés Urquidi", "Andrés Uriquidi|Andrés Urquidi Selich", "Directores/as", "M", ""),
    ("Katherine Mercado", "Katherine Mercado Rocha", "Directores/as", "F", ""),
    ("Mercedes Carranza", "Mercedes Carranza Aguayo", "Directores/as", "F", ""),
    ("Marcela Cabrerizo", "Marcela Cabrerizo Uzín", "Directores/as", "F", ""),
    ("Ricardo Villavicencio", "Ricardo Villavicencio Núñez", "Comisión Fiscalizadora", "M", ""),
    ("Alvaro Bazán", "Álvaro Bazán Auza", "Comisión Fiscalizadora", "M", ""),
    ("Enrique Palmero", "Enrique Palmero, GGL|Enrique Palmero Pantoja", "Alta Gerencia", "M", "Gerente General"),
    ("Ninozka Villegas", "Sinozka Villegas, GNAI|Ninozka Villegas Gironda", "Alta Gerencia", "F", "Gerenta Nacional de Auditoría Interna"),
    ("Davor Saric", "Davor Saric, GNRI|Davor Saric Yaksic", "Alta Gerencia", "M", "Gerente Nacional de Riesgo Integral"),
    ("René Calvo", "René Calvo, GDN|René Calvo Sainz", "Alta Gerencia", "M", "Gerente de División de Negocios"),
    ("Liliana Riveros", "Liliana Riveros, GNO|Liliana Riveros Haydar", "Alta Gerencia", "F", "Gerenta Nacional de Operaciones"),
    ("Mariela Soliz", "Mariela Soliz, GNME|Mariela Soliz Gumiel", "Alta Gerencia", "F", "Gerenta Nacional de Marketing Estratégico"),
    ("Diego Mariscal", "Diego Mariscal, SNGE|Diego Mariscal Gutierrez", "Administración", "M", "Subgerente Nacional de Gestión Estratégica"),
    ("Alejandro Collao", "Alejandro Collao, GNAJ", "Administración", "M", ""),
    ("Claudia Escobar", "Claudia Escobar, APD|Claudia Escobar Valdez", "Administración", "F", "Analista de Presidencia de Directorio"),
]
for row in data:
    sheet.append(row)

import io
buffer = io.BytesIO()
wb.save(buffer)
sharepoint_client.upload_file("Actas", "Catalogo_Personas.xlsx", buffer.getvalue())
print("Catálogo creado y subido a SharePoint.")