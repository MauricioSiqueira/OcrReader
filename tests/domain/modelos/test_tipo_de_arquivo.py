"""Testes do catálogo de MIME types de `TipoDeArquivo`."""

from __future__ import annotations

import pytest

from ocr_reader.domain.modelos.tipo_de_arquivo import (
    TipoDeArquivo,
    tipo_de_arquivo_a_partir_do_mime,
)


@pytest.mark.parametrize(
    ("mime_type", "tipo_esperado"),
    [
        ("application/pdf", TipoDeArquivo.PDF),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            TipoDeArquivo.DOCX,
        ),
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            TipoDeArquivo.XLSX,
        ),
        (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            TipoDeArquivo.PPTX,
        ),
        ("text/html", TipoDeArquivo.HTML),
        ("image/jpeg", TipoDeArquivo.JPEG),
        ("image/png", TipoDeArquivo.PNG),
        ("image/bmp", TipoDeArquivo.BMP),
        ("image/x-ms-bmp", TipoDeArquivo.BMP),
        ("image/tiff", TipoDeArquivo.TIFF),
        ("image/heic", TipoDeArquivo.HEIF),
        ("image/heif", TipoDeArquivo.HEIF),
    ],
)
def test_tipo_de_arquivo_a_partir_do_mime_com_mime_aceito_retorna_tipo_correspondente(
    mime_type: str, tipo_esperado: TipoDeArquivo
) -> None:
    assert tipo_de_arquivo_a_partir_do_mime(mime_type) is tipo_esperado


@pytest.mark.parametrize(
    "mime_type",
    ["application/zip", "application/x-msdownload", "application/octet-stream", "text/plain"],
)
def test_tipo_de_arquivo_a_partir_do_mime_com_mime_nao_aceito_retorna_none(
    mime_type: str,
) -> None:
    assert tipo_de_arquivo_a_partir_do_mime(mime_type) is None
