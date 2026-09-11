"""Testes do caso de uso `ConsultarExtracaoDeTexto`."""

from __future__ import annotations

import pytest

from ocr_reader.application.casos_de_uso.consultar_extracao_de_texto import (
    ConsultarExtracaoDeTexto,
)
from ocr_reader.domain.erros import ExtracaoNaoEncontrada, ServicoDeOcrIndisponivel
from ocr_reader.domain.modelos.extracao import (
    IdentificadorDaExtracao,
    ResultadoDaExtracao,
    SituacaoDaExtracao,
)
from tests.dubles_de_portas import ServicoDeOcrFalso

_IDENTIFICADOR = IdentificadorDaExtracao(valor="op-123")


async def test_executar_com_extracao_processando_repassa_o_resultado() -> None:
    servico_de_ocr = ServicoDeOcrFalso(
        resultado=ResultadoDaExtracao(situacao=SituacaoDaExtracao.PROCESSANDO)
    )
    caso_de_uso = ConsultarExtracaoDeTexto(servico_de_ocr)

    resultado = await caso_de_uso.executar(_IDENTIFICADOR)

    assert resultado.situacao is SituacaoDaExtracao.PROCESSANDO
    assert resultado.texto is None


async def test_executar_com_extracao_concluida_repassa_o_texto() -> None:
    servico_de_ocr = ServicoDeOcrFalso(
        resultado=ResultadoDaExtracao(situacao=SituacaoDaExtracao.CONCLUIDA, texto="ola mundo")
    )
    caso_de_uso = ConsultarExtracaoDeTexto(servico_de_ocr)

    resultado = await caso_de_uso.executar(_IDENTIFICADOR)

    assert resultado.situacao is SituacaoDaExtracao.CONCLUIDA
    assert resultado.texto == "ola mundo"


async def test_executar_com_extracao_que_falhou_levanta_servico_de_ocr_indisponivel() -> None:
    servico_de_ocr = ServicoDeOcrFalso(
        resultado=ResultadoDaExtracao(situacao=SituacaoDaExtracao.FALHOU)
    )
    caso_de_uso = ConsultarExtracaoDeTexto(servico_de_ocr)

    with pytest.raises(ServicoDeOcrIndisponivel):
        await caso_de_uso.executar(_IDENTIFICADOR)


async def test_executar_com_identificador_desconhecido_propaga_extracao_nao_encontrada() -> None:
    servico_de_ocr = ServicoDeOcrFalso(
        excecao_na_consulta=ExtracaoNaoEncontrada("não existe extração com esse id")
    )
    caso_de_uso = ConsultarExtracaoDeTexto(servico_de_ocr)

    with pytest.raises(ExtracaoNaoEncontrada):
        await caso_de_uso.executar(_IDENTIFICADOR)
