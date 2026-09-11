"""Testes do caso de uso `SolicitarExtracaoDeTexto`.

Usa uma instância real de `ValidarDocumentoRemoto` (com dublês das portas de baixo nível) para
comprovar composição de verdade: a validação não é reimplementada aqui, apenas reaproveitada.
"""

from __future__ import annotations

import pytest

from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import (
    SolicitarExtracaoDeTexto,
)
from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.domain.erros import ServicoDeOcrIndisponivel, TipoDeArquivoNaoSuportado
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import IdentificadorDaExtracao
from ocr_reader.domain.modelos.resultado_da_deteccao import ResultadoDaDeteccao
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from tests.dubles_de_portas import DetectorDeTipoFalso, LeitorDeBytesFalso, ServicoDeOcrFalso

_JANELA_DE_CABECALHO_EM_BYTES = 8
_JANELA_AMPLIADA_EM_BYTES = 32
_TAMANHO_MAXIMO_EM_BYTES = 1_000

_ENDERECO = EnderecoDeBlob.criar(
    "https://conta.blob.core.windows.net/container/arquivo.pdf?sig=abc", ["*.blob.core.windows.net"]
)


def _criar_validador(detector: DetectorDeTipoFalso) -> ValidarDocumentoRemoto:
    return ValidarDocumentoRemoto(
        leitor_de_bytes=LeitorDeBytesFalso(conteudo_do_blob=b"%PDF-1.4"),
        detector_de_tipo=detector,
        tamanho_maximo_em_bytes=_TAMANHO_MAXIMO_EM_BYTES,
        janela_de_cabecalho_em_bytes=_JANELA_DE_CABECALHO_EM_BYTES,
        janela_ampliada_em_bytes=_JANELA_AMPLIADA_EM_BYTES,
    )


async def test_executar_com_documento_valido_solicita_leitura_e_retorna_identificador() -> None:
    validador = _criar_validador(DetectorDeTipoFalso([ResultadoDaDeteccao(tipo=TipoDeArquivo.PDF)]))
    servico_de_ocr = ServicoDeOcrFalso(identificador=IdentificadorDaExtracao(valor="op-123"))
    caso_de_uso = SolicitarExtracaoDeTexto(validador, servico_de_ocr)

    extracao_solicitada = await caso_de_uso.executar(_ENDERECO)

    assert extracao_solicitada.identificador.valor == "op-123"
    assert extracao_solicitada.tipo_de_arquivo is TipoDeArquivo.PDF
    assert extracao_solicitada.tamanho_em_bytes == len(b"%PDF-1.4")
    assert servico_de_ocr.chamadas_de_solicitacao == 1


async def test_executar_com_documento_rejeitado_nao_chama_o_servico_de_ocr() -> None:
    validador = _criar_validador(DetectorDeTipoFalso([ResultadoDaDeteccao(tipo=None)]))
    servico_de_ocr = ServicoDeOcrFalso(
        identificador=IdentificadorDaExtracao(valor="nao-deveria-sair")
    )
    caso_de_uso = SolicitarExtracaoDeTexto(validador, servico_de_ocr)

    with pytest.raises(TipoDeArquivoNaoSuportado):
        await caso_de_uso.executar(_ENDERECO)

    assert servico_de_ocr.chamadas_de_solicitacao == 0


async def test_executar_com_falha_na_submissao_propaga_servico_de_ocr_indisponivel() -> None:
    validador = _criar_validador(DetectorDeTipoFalso([ResultadoDaDeteccao(tipo=TipoDeArquivo.PDF)]))
    servico_de_ocr = ServicoDeOcrFalso(
        excecao_na_solicitacao=ServicoDeOcrIndisponivel("falha simulada")
    )
    caso_de_uso = SolicitarExtracaoDeTexto(validador, servico_de_ocr)

    with pytest.raises(ServicoDeOcrIndisponivel):
        await caso_de_uso.executar(_ENDERECO)
