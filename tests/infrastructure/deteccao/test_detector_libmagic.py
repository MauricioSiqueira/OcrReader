"""Testes do adaptador `DetectorLibmagic`, contra a biblioteca `libmagic` real."""

from __future__ import annotations

from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from ocr_reader.infrastructure.deteccao.detector_libmagic import DetectorLibmagic


def test_detector_libmagic_com_pdf_detecta_tipo_pdf(pdf_minimo: bytes) -> None:
    resultado = DetectorLibmagic().detectar(pdf_minimo)

    assert resultado.tipo is TipoDeArquivo.PDF
    assert resultado.ambiguo is False


def test_detector_libmagic_com_png_detecta_tipo_png(png_minimo: bytes) -> None:
    resultado = DetectorLibmagic().detectar(png_minimo)

    assert resultado.tipo is TipoDeArquivo.PNG


def test_detector_libmagic_com_jpeg_detecta_tipo_jpeg(jpeg_minimo: bytes) -> None:
    resultado = DetectorLibmagic().detectar(jpeg_minimo)

    assert resultado.tipo is TipoDeArquivo.JPEG


def test_detector_libmagic_com_docx_detecta_tipo_docx(docx_minimo: bytes) -> None:
    resultado = DetectorLibmagic().detectar(docx_minimo)

    assert resultado.tipo is TipoDeArquivo.DOCX
    assert resultado.ambiguo is False


def test_detector_libmagic_com_xlsx_detecta_tipo_xlsx(xlsx_minimo: bytes) -> None:
    resultado = DetectorLibmagic().detectar(xlsx_minimo)

    assert resultado.tipo is TipoDeArquivo.XLSX
    assert resultado.ambiguo is False


def test_detector_libmagic_com_zip_comum_marca_resultado_como_ambiguo(zip_comum: bytes) -> None:
    resultado = DetectorLibmagic().detectar(zip_comum)

    assert resultado.tipo is None
    assert resultado.ambiguo is True


def test_detector_libmagic_com_bytes_de_executavel_nao_detecta_tipo_aceito() -> None:
    cabecalho_de_executavel_elf = bytes.fromhex("7f454c46020101000000000000000000")

    resultado = DetectorLibmagic().detectar(cabecalho_de_executavel_elf)

    assert resultado.tipo is None
    assert resultado.ambiguo is False
