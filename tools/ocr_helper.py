# tools/ocr_helper.py — reemplazar todo el archivo
"""OCR de respaldo para PDFs escaneados (sin capa de texto), usando Azure
AI Document Intelligence en vez de un binario local — funciona igual en
local que desplegado en Azure Functions, sin depender de instalar nada en
el sistema operativo."""
from __future__ import annotations

import logging

import fitz  # PyMuPDF
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

from .config import get_env

logger = logging.getLogger(__name__)

_MIN_TEXT_LENGTH_TO_SKIP_OCR = 50


def extract_text_with_ocr_fallback(pdf_bytes: bytes) -> str:
    """Intenta extracción directa de texto; si el resultado es muy corto
    (PDF escaneado), envía el documento a Azure Document Intelligence."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    direct_text = "\n".join(page.get_text() for page in doc)

    if len(direct_text.strip()) >= _MIN_TEXT_LENGTH_TO_SKIP_OCR:
        return direct_text

    logger.info("Texto directo insuficiente (%d caracteres) — aplicando Document Intelligence.", len(direct_text.strip()))
    return _ocr_with_document_intelligence(pdf_bytes)


def _ocr_with_document_intelligence(pdf_bytes: bytes) -> str:
    client = DocumentIntelligenceClient(
        endpoint=get_env("AZURE_DOCINT_ENDPOINT"),
        credential=AzureKeyCredential(get_env("AZURE_DOCINT_KEY")),
    )

    poller = client.begin_analyze_document(
        "prebuilt-read",
        AnalyzeDocumentRequest(bytes_source=pdf_bytes),
    )
    result = poller.result()

    return result.content or ""