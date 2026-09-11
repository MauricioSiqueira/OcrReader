"""Fixtures binárias mínimas compartilhadas pelos testes."""

from __future__ import annotations

import pytest

from tests.construtores_de_fixtures_binarias import (
    construir_docx_minimo,
    construir_jpeg_minimo,
    construir_pdf_minimo,
    construir_png_minimo,
    construir_xlsx_minimo,
    construir_zip_comum,
)


@pytest.fixture
def pdf_minimo() -> bytes:
    return construir_pdf_minimo()


@pytest.fixture
def png_minimo() -> bytes:
    return construir_png_minimo()


@pytest.fixture
def jpeg_minimo() -> bytes:
    return construir_jpeg_minimo()


@pytest.fixture
def docx_minimo() -> bytes:
    return construir_docx_minimo()


@pytest.fixture
def xlsx_minimo() -> bytes:
    return construir_xlsx_minimo()


@pytest.fixture
def zip_comum() -> bytes:
    return construir_zip_comum()
