# tools/ocr_helper.py
"""OCR de respaldo para PDFs escaneados (sin capa de texto). Se usa cuando
la extracción directa de PyMuPDF devuelve muy poco texto, señal de que el
PDF es una imagen (documento firmado y escaneado)."""
from __future__ import annotations

import io
import logging
import os

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

# En Windows, pytesseract necesita saber dónde está el ejecutable.
# Ajusta esta ruta si instalaste Tesseract en otro lugar.
_TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
if os.path.exists(_TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

_MIN_TEXT_LENGTH_TO_SKIP_OCR = 50  # si hay menos texto que esto, se asume escaneado


def extract_text_with_ocr_fallback(pdf_bytes: bytes, dpi: int = 300) -> str:
    """Intenta extracción directa de texto; si el resultado es muy corto
    (PDF escaneado), rasteriza cada página y aplica OCR en español."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    direct_text = "\n".join(page.get_text() for page in doc)

    if len(direct_text.strip()) >= _MIN_TEXT_LENGTH_TO_SKIP_OCR:
        return direct_text

    logger.info("Texto directo insuficiente (%d caracteres) — aplicando OCR.", len(direct_text.strip()))
    ocr_parts = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        page_text = pytesseract.image_to_string(image, lang="spa")
        ocr_parts.append(page_text)

    return "\n".join(ocr_parts)