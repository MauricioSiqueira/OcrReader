"""Tipos de arquivo aceitos para extração de texto e seus MIME types associados."""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType


class TipoDeArquivo(Enum):
    """Formatos de documento aceitos pelo Azure Document Intelligence (`prebuilt-read`)."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    HEIF = "heif"


_CATALOGO_DE_MIME_TYPES: MappingProxyType[str, TipoDeArquivo] = MappingProxyType(
    {
        "application/pdf": TipoDeArquivo.PDF,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
            TipoDeArquivo.DOCX
        ),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": TipoDeArquivo.XLSX,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": (
            TipoDeArquivo.PPTX
        ),
        "text/html": TipoDeArquivo.HTML,
        "image/jpeg": TipoDeArquivo.JPEG,
        "image/png": TipoDeArquivo.PNG,
        "image/bmp": TipoDeArquivo.BMP,
        "image/x-ms-bmp": TipoDeArquivo.BMP,
        "image/tiff": TipoDeArquivo.TIFF,
        "image/heic": TipoDeArquivo.HEIF,
        "image/heif": TipoDeArquivo.HEIF,
    }
)

# MIME types que um contêiner ZIP genérico pode assumir antes de ser distinguido de um OOXML
# (DOCX/XLSX/PPTX) — a "armadilha do OOXML" descrita no plano.
MIME_TYPES_ZIP_AMBIGUOS: frozenset[str] = frozenset(
    {"application/zip", "application/x-zip-compressed"}
)


def tipo_de_arquivo_a_partir_do_mime(mime_type: str) -> TipoDeArquivo | None:
    """Traduz um MIME type detectado para o `TipoDeArquivo` correspondente.

    Args:
        mime_type: MIME type retornado pela detecção de magic bytes.

    Returns:
        O `TipoDeArquivo` correspondente, ou `None` se o MIME type não é aceito.
    """
    return _CATALOGO_DE_MIME_TYPES.get(mime_type)
