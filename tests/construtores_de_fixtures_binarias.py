"""Construtores de arquivos binários mínimos usados como fixtures nos testes.

Os arquivos são construídos em memória (em vez de commitados como blobs binários no
repositório) para que o conteúdo de cada fixture continue revisável como código.
"""

from __future__ import annotations

import io
import struct
import zipfile
import zlib

_TIPO_DE_CONTEUDO_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
_TIPO_DE_CONTEUDO_XLSX = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
)


def construir_pdf_minimo() -> bytes:
    """Constrói um PDF minúsculo, suficiente para detecção por magic bytes."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 3 3]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n"
        b"%%EOF"
    )


def construir_png_minimo() -> bytes:
    """Constrói um PNG de 1x1 pixel: assinatura + chunk IHDR válido."""
    assinatura = b"\x89PNG\r\n\x1a\n"
    dados_do_ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return assinatura + _construir_chunk_png(b"IHDR", dados_do_ihdr)


def _construir_chunk_png(tipo: bytes, dados: bytes) -> bytes:
    tamanho = struct.pack(">I", len(dados))
    crc = struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    return tamanho + tipo + dados + crc


def construir_jpeg_minimo() -> bytes:
    """Constrói um JPEG mínimo: marcador SOI + APP0 (JFIF) + EOI."""
    return bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\xff\xd9"


def construir_docx_minimo() -> bytes:
    """Constrói um DOCX mínimo: ZIP OOXML com `word/document.xml`."""
    conteudo_da_parte_principal = (
        '<?xml version="1.0"?><w:document xmlns:w="x"><w:body/></w:document>'
    )
    return _construir_zip_ooxml_minimo(
        nome_da_parte_principal="word/document.xml",
        conteudo_da_parte_principal=conteudo_da_parte_principal,
        tipo_de_conteudo_da_parte_principal=_TIPO_DE_CONTEUDO_DOCX,
    )


def construir_xlsx_minimo() -> bytes:
    """Constrói um XLSX mínimo: ZIP OOXML com `xl/workbook.xml`."""
    return _construir_zip_ooxml_minimo(
        nome_da_parte_principal="xl/workbook.xml",
        conteudo_da_parte_principal='<?xml version="1.0"?><workbook xmlns="x"/>',
        tipo_de_conteudo_da_parte_principal=_TIPO_DE_CONTEUDO_XLSX,
    )


def construir_zip_comum() -> bytes:
    """Constrói um ZIP comum, sem nenhuma marca de OOXML — deve ser rejeitado."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as arquivo_zip:
        arquivo_zip.writestr("leiame.txt", "só um arquivo comum, nada de office aqui")
    return buffer.getvalue()


def _construir_zip_ooxml_minimo(
    nome_da_parte_principal: str,
    conteudo_da_parte_principal: str,
    tipo_de_conteudo_da_parte_principal: str,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as arquivo_zip:
        arquivo_zip.writestr(
            "[Content_Types].xml",
            _content_types_xml(nome_da_parte_principal, tipo_de_conteudo_da_parte_principal),
        )
        arquivo_zip.writestr("_rels/.rels", _rels_minimos(nome_da_parte_principal))
        arquivo_zip.writestr(nome_da_parte_principal, conteudo_da_parte_principal)
    return buffer.getvalue()


def _content_types_xml(nome_da_parte_principal: str, tipo_de_conteudo: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/{nome_da_parte_principal}" ContentType="{tipo_de_conteudo}"/>'
        "</Types>"
    )


def _rels_minimos(nome_da_parte_principal: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        f'Target="{nome_da_parte_principal}"/>'
        "</Relationships>"
    )
