"""Fábrica da aplicação FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from fastapi import FastAPI

from ocr_reader.application.casos_de_uso.consultar_extracao_de_texto import (
    ConsultarExtracaoDeTexto,
)
from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import (
    SolicitarExtracaoDeTexto,
)
from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.infrastructure.azure.servico_de_ocr_document_intelligence import (
    ServicoDeOcrDocumentIntelligence,
)
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.infrastructure.deteccao.detector_libmagic import DetectorLibmagic
from ocr_reader.infrastructure.http.leitor_de_bytes_httpx import LeitorDeBytesHttpx
from ocr_reader.infrastructure.observabilidade.log_estruturado import configurar_log
from ocr_reader.interfaces.api.rotas.extracoes import roteador as roteador_de_extracoes
from ocr_reader.interfaces.api.tratadores_de_erro import registrar_tratadores_de_erro


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Cria os adaptadores de infraestrutura na subida e os libera no encerramento."""
    configuracao = Configuracao()
    cliente_http = httpx.AsyncClient(timeout=configuracao.timeout_em_segundos)
    cliente_azure = DocumentIntelligenceClient(
        configuracao.endpoint_do_document_intelligence,
        AzureKeyCredential(configuracao.chave_do_document_intelligence.get_secret_value()),
    )

    validar_documento_remoto = ValidarDocumentoRemoto(
        leitor_de_bytes=LeitorDeBytesHttpx(cliente_http),
        detector_de_tipo=DetectorLibmagic(),
        tamanho_maximo_em_bytes=configuracao.tamanho_maximo_em_bytes,
        janela_de_cabecalho_em_bytes=configuracao.janela_de_cabecalho_em_bytes,
        janela_ampliada_em_bytes=configuracao.janela_ampliada_em_bytes,
    )
    servico_de_ocr = ServicoDeOcrDocumentIntelligence(
        cliente=cliente_azure,
        id_do_modelo=configuracao.id_do_modelo_de_ocr,
        versao_da_api=configuracao.versao_da_api_de_ocr,
    )

    app.state.configuracao = configuracao
    app.state.caso_de_uso_de_solicitacao = SolicitarExtracaoDeTexto(
        validar_documento_remoto=validar_documento_remoto, servico_de_ocr=servico_de_ocr
    )
    app.state.caso_de_uso_de_consulta = ConsultarExtracaoDeTexto(servico_de_ocr=servico_de_ocr)

    try:
        yield
    finally:
        await cliente_http.aclose()
        await cliente_azure.close()


def criar_aplicacao() -> FastAPI:
    """Constrói a instância da aplicação FastAPI com rotas e tratadores de erro registrados."""
    configurar_log()
    app = FastAPI(title="ocr-reader", lifespan=_ciclo_de_vida)
    app.include_router(roteador_de_extracoes)
    registrar_tratadores_de_erro(app)
    return app


app = criar_aplicacao()
