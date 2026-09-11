"""Fábrica da aplicação FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.infrastructure.deteccao.detector_libmagic import DetectorLibmagic
from ocr_reader.infrastructure.http.leitor_de_bytes_httpx import LeitorDeBytesHttpx
from ocr_reader.interfaces.api.rotas.extracoes import roteador as roteador_de_extracoes
from ocr_reader.interfaces.api.tratadores_de_erro import registrar_tratadores_de_erro


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Cria os adaptadores de infraestrutura na subida e os libera no encerramento."""
    configuracao = Configuracao()
    cliente_http = httpx.AsyncClient(timeout=configuracao.timeout_em_segundos)

    app.state.configuracao = configuracao
    app.state.caso_de_uso_de_validacao = ValidarDocumentoRemoto(
        leitor_de_bytes=LeitorDeBytesHttpx(cliente_http),
        detector_de_tipo=DetectorLibmagic(),
        tamanho_maximo_em_bytes=configuracao.tamanho_maximo_em_bytes,
        janela_de_cabecalho_em_bytes=configuracao.janela_de_cabecalho_em_bytes,
        janela_ampliada_em_bytes=configuracao.janela_ampliada_em_bytes,
    )

    try:
        yield
    finally:
        await cliente_http.aclose()


def criar_aplicacao() -> FastAPI:
    """Constrói a instância da aplicação FastAPI com rotas e tratadores de erro registrados."""
    app = FastAPI(title="ocr-reader", lifespan=_ciclo_de_vida)
    app.include_router(roteador_de_extracoes)
    registrar_tratadores_de_erro(app)
    return app


app = criar_aplicacao()
