"""Testes do log estruturado emitido pelas rotas de extração.

Usa `capsys` (não `caplog`) porque o que importa aqui é o texto que realmente sai pelo stdout do
processo — exatamente o que um agregador de log recolheria — e não a representação interna que o
`caplog` do pytest monta a partir do `LogRecord`.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import ExtracaoSolicitada
from ocr_reader.domain.modelos.extracao import (
    IdentificadorDaExtracao,
    MetricasDaExtracao,
    ResultadoDaExtracao,
    SituacaoDaExtracao,
)
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.interfaces.api.aplicacao import criar_aplicacao
from ocr_reader.interfaces.api.dependencias import (
    obter_caso_de_uso_de_consulta,
    obter_caso_de_uso_de_solicitacao,
    obter_configuracao,
)

_ASSINATURA_SECRETA = "assinatura-secreta-de-teste-nao-pode-vazar"
_URI_VALIDO = f"https://conta.blob.core.windows.net/container/arquivo.pdf?sig={_ASSINATURA_SECRETA}"
_CHAVE_SECRETA_DA_AZURE = "chave-secreta-do-document-intelligence-nao-pode-vazar"
_CONFIGURACAO_DE_TESTE = Configuracao(hosts_permitidos=["*.blob.core.windows.net"])


class _CasoDeUsoDeSolicitacaoFalso:
    def __init__(self, extracao_solicitada: ExtracaoSolicitada) -> None:
        self._extracao_solicitada = extracao_solicitada

    async def executar(self, endereco: object) -> ExtracaoSolicitada:
        return self._extracao_solicitada


class _CasoDeUsoDeConsultaFalso:
    def __init__(self, resultado: ResultadoDaExtracao) -> None:
        self._resultado = resultado

    async def executar(self, identificador: IdentificadorDaExtracao) -> ResultadoDaExtracao:
        return self._resultado


def _criar_cliente(
    monkeypatch: pytest.MonkeyPatch,
    caso_de_uso_de_solicitacao: _CasoDeUsoDeSolicitacaoFalso | None = None,
    caso_de_uso_de_consulta: _CasoDeUsoDeConsultaFalso | None = None,
) -> TestClient:
    # A configuração real (com a chave) é a que o lifespan constrói de verdade a partir do
    # ambiente — é ela que precisa provar que nunca vaza, não a que sobrescrevemos na rota.
    monkeypatch.setenv("OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE", _CHAVE_SECRETA_DA_AZURE)
    monkeypatch.setenv(
        "OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE", "https://endpoint-de-teste.example.com"
    )

    app = criar_aplicacao()
    app.dependency_overrides[obter_configuracao] = lambda: _CONFIGURACAO_DE_TESTE
    if caso_de_uso_de_solicitacao is not None:
        app.dependency_overrides[obter_caso_de_uso_de_solicitacao] = (
            lambda: caso_de_uso_de_solicitacao
        )
    if caso_de_uso_de_consulta is not None:
        app.dependency_overrides[obter_caso_de_uso_de_consulta] = lambda: caso_de_uso_de_consulta
    return TestClient(app)


def _linhas_json_do_log(saida_padrao: str) -> list[dict[str, Any]]:
    return [json.loads(linha) for linha in saida_padrao.splitlines() if linha.strip()]


def test_post_extracoes_emite_evento_extracao_solicitada_em_json_valido(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        ExtracaoSolicitada(
            identificador=IdentificadorDaExtracao(valor="op-123"),
            tipo_de_arquivo=TipoDeArquivo.PDF,
            tamanho_em_bytes=54321,
        )
    )

    with _criar_cliente(monkeypatch, caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 202
    linhas = _linhas_json_do_log(capsys.readouterr().out)
    eventos = [linha for linha in linhas if linha.get("evento") == "extracao_solicitada"]

    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["id_extracao"] == "op-123"
    assert evento["tipo_de_arquivo"] == "pdf"
    assert evento["tamanho_em_bytes"] == 54321
    assert {"timestamp", "nivel", "mensagem"} <= evento.keys()


def test_get_extracao_concluida_emite_evento_extracao_concluida_em_json_valido(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        ResultadoDaExtracao(
            situacao=SituacaoDaExtracao.CONCLUIDA,
            texto="ola mundo",
            metricas=MetricasDaExtracao(duracao_do_ocr_em_ms=1500, quantidade_de_paginas=3),
        )
    )

    with _criar_cliente(monkeypatch, caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/op-123")

    assert resposta.status_code == 200
    linhas = _linhas_json_do_log(capsys.readouterr().out)
    eventos = [linha for linha in linhas if linha.get("evento") == "extracao_concluida"]
    assert len(eventos) == 1
    assert eventos[0]["id_extracao"] == "op-123"
    assert eventos[0]["duracao_do_ocr_em_ms"] == 1500
    assert eventos[0]["quantidade_de_paginas"] == 3


def test_get_extracao_concluida_sem_metricas_nao_emite_evento_mas_responde_normalmente(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        ResultadoDaExtracao(situacao=SituacaoDaExtracao.CONCLUIDA, texto="ola mundo", metricas=None)
    )

    with _criar_cliente(monkeypatch, caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/op-123")

    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "concluida", "texto": "ola mundo"}
    linhas = _linhas_json_do_log(capsys.readouterr().out)
    assert not any(linha.get("evento") == "extracao_concluida" for linha in linhas)


def test_nenhuma_linha_de_log_contem_o_sas_uri_ou_a_chave_da_azure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    caso_de_uso_de_solicitacao = _CasoDeUsoDeSolicitacaoFalso(
        ExtracaoSolicitada(
            identificador=IdentificadorDaExtracao(valor="op-123"),
            tipo_de_arquivo=TipoDeArquivo.PDF,
            tamanho_em_bytes=54321,
        )
    )
    caso_de_uso_de_consulta = _CasoDeUsoDeConsultaFalso(
        ResultadoDaExtracao(
            situacao=SituacaoDaExtracao.CONCLUIDA,
            texto="ola mundo",
            metricas=MetricasDaExtracao(duracao_do_ocr_em_ms=1500, quantidade_de_paginas=3),
        )
    )

    with _criar_cliente(
        monkeypatch,
        caso_de_uso_de_solicitacao=caso_de_uso_de_solicitacao,
        caso_de_uso_de_consulta=caso_de_uso_de_consulta,
    ) as cliente:
        cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})
        cliente.get("/extracoes/op-123")

    saida_padrao = capsys.readouterr().out

    assert _ASSINATURA_SECRETA not in saida_padrao
    assert "sig=" not in saida_padrao
    assert _CHAVE_SECRETA_DA_AZURE not in saida_padrao
    # Todas as linhas continuam sendo JSON válido, mesmo com a checagem de vazamento acima.
    assert _linhas_json_do_log(saida_padrao)
