"""Testes do adaptador `ServicoDeOcrDocumentIntelligence`, contra um servidor local real.

Nenhum teste aqui faz requisição à Azure de verdade: `ServidorDocumentIntelligenceFalso` sobe um
servidor HTTP real em `127.0.0.1`, e o `DocumentIntelligenceClient` fala com ele como se fosse o
serviço, exercitando o adaptador e o SDK de ponta a ponta sem sair da máquina.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from ocr_reader.domain.erros import ExtracaoNaoEncontrada, ServicoDeOcrIndisponivel
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import IdentificadorDaExtracao, SituacaoDaExtracao
from ocr_reader.infrastructure.azure.servico_de_ocr_document_intelligence import (
    ServicoDeOcrDocumentIntelligence,
)
from tests.infrastructure.azure.servidor_document_intelligence_falso import (
    ID_DO_MODELO,
    VERSAO_DA_API,
    ServidorDocumentIntelligenceFalso,
)

_ENDERECO = EnderecoDeBlob.criar(
    "https://conta.blob.core.windows.net/container/arquivo.pdf?sig=abc",
    ["*.blob.core.windows.net"],
)


@pytest.fixture
async def servidor() -> AsyncIterator[ServidorDocumentIntelligenceFalso]:
    instancia = ServidorDocumentIntelligenceFalso()
    await instancia.iniciar()
    try:
        yield instancia
    finally:
        await instancia.encerrar()


@pytest.fixture
async def servico(
    servidor: ServidorDocumentIntelligenceFalso,
) -> AsyncIterator[ServicoDeOcrDocumentIntelligence]:
    cliente = DocumentIntelligenceClient(servidor.endpoint, AzureKeyCredential("chave-de-teste"))
    try:
        yield ServicoDeOcrDocumentIntelligence(
            cliente=cliente, id_do_modelo=ID_DO_MODELO, versao_da_api=VERSAO_DA_API
        )
    finally:
        await cliente.close()


async def test_solicitar_leitura_com_submissao_aceita_retorna_identificador(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    identificador = await servico.solicitar_leitura(_ENDERECO)

    assert identificador.valor == servidor.operation_id


async def test_solicitar_leitura_com_submissao_falhando_levanta_servico_indisponivel(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.falhar_submissao = True

    with pytest.raises(ServicoDeOcrIndisponivel):
        await servico.solicitar_leitura(_ENDERECO)


async def test_obter_leitura_processando_retorna_resultado_processando(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.corpo_da_consulta = {"status": "running"}

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.situacao is SituacaoDaExtracao.PROCESSANDO
    assert resultado.texto is None


async def test_obter_leitura_concluida_retorna_resultado_com_texto(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.corpo_da_consulta = {
        "status": "succeeded",
        "analyzeResult": {"content": "ola mundo"},
    }

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.situacao is SituacaoDaExtracao.CONCLUIDA
    assert resultado.texto == "ola mundo"
    assert resultado.metricas is None


async def test_obter_leitura_concluida_com_datas_e_paginas_calcula_metricas(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    # Formato real de resposta do Azure: ISO 8601 com sufixo "Z" e frações de segundo.
    servidor.corpo_da_consulta = {
        "status": "succeeded",
        "createdDateTime": "2026-01-01T10:00:00.000Z",
        "lastUpdatedDateTime": "2026-01-01T10:00:03.250Z",
        "analyzeResult": {"content": "ola mundo", "pages": [{}, {}, {}]},
    }

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.metricas is not None
    assert resultado.metricas.duracao_do_ocr_em_ms == 3250
    assert resultado.metricas.quantidade_de_paginas == 3


async def test_obter_leitura_concluida_sem_datas_retorna_metricas_none_sem_quebrar(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.corpo_da_consulta = {
        "status": "succeeded",
        "analyzeResult": {"content": "ola mundo", "pages": [{}, {}, {}]},
    }

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.situacao is SituacaoDaExtracao.CONCLUIDA
    assert resultado.texto == "ola mundo"
    assert resultado.metricas is None


async def test_obter_leitura_concluida_sem_pages_retorna_metricas_none_sem_quebrar(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.corpo_da_consulta = {
        "status": "succeeded",
        "createdDateTime": "2026-01-01T10:00:00Z",
        "lastUpdatedDateTime": "2026-01-01T10:00:03Z",
        "analyzeResult": {"content": "ola mundo"},
    }

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.situacao is SituacaoDaExtracao.CONCLUIDA
    assert resultado.metricas is None


async def test_obter_leitura_com_status_failed_retorna_resultado_com_situacao_falhou(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.corpo_da_consulta = {"status": "failed"}

    resultado = await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))

    assert resultado.situacao is SituacaoDaExtracao.FALHOU


async def test_obter_leitura_com_id_inexistente_levanta_extracao_nao_encontrada(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.status_http_da_consulta = 404
    servidor.corpo_da_consulta = {"error": {"message": "not found"}}

    with pytest.raises(ExtracaoNaoEncontrada):
        await servico.obter_leitura(IdentificadorDaExtracao(valor="nao-existe"))


async def test_obter_leitura_com_erro_do_servico_levanta_servico_indisponivel(
    servidor: ServidorDocumentIntelligenceFalso, servico: ServicoDeOcrDocumentIntelligence
) -> None:
    servidor.status_http_da_consulta = 500
    servidor.corpo_da_consulta = {"error": {"message": "falha interna simulada"}}

    with pytest.raises(ServicoDeOcrIndisponivel):
        await servico.obter_leitura(IdentificadorDaExtracao(valor=servidor.operation_id))
