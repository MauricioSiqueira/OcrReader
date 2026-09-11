"""Testes do caso de uso `ValidarDocumentoRemoto`, com dublês das portas de domínio."""

from __future__ import annotations

import pytest

from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.domain.erros import (
    ArquivoExcedeLimite,
    DocumentoInacessivel,
    TipoDeArquivoNaoSuportado,
)
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.resultado_da_deteccao import ResultadoDaDeteccao
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from tests.dubles_de_portas import DetectorDeTipoFalso, LeitorDeBytesFalso, LeitorDeBytesQueFalha

_JANELA_DE_CABECALHO_EM_BYTES = 8
_JANELA_AMPLIADA_EM_BYTES = 32
_TAMANHO_MAXIMO_EM_BYTES = 1_000

_ENDERECO = EnderecoDeBlob.criar(
    "https://conta.blob.core.windows.net/container/arquivo?sig=abc", ["*.blob.core.windows.net"]
)


def _criar_caso_de_uso(
    leitor_de_bytes: LeitorDeBytesFalso | LeitorDeBytesQueFalha,
    detector_de_tipo: DetectorDeTipoFalso,
) -> ValidarDocumentoRemoto:
    return ValidarDocumentoRemoto(
        leitor_de_bytes=leitor_de_bytes,
        detector_de_tipo=detector_de_tipo,
        tamanho_maximo_em_bytes=_TAMANHO_MAXIMO_EM_BYTES,
        janela_de_cabecalho_em_bytes=_JANELA_DE_CABECALHO_EM_BYTES,
        janela_ampliada_em_bytes=_JANELA_AMPLIADA_EM_BYTES,
    )


async def test_executar_com_tipo_reconhecido_de_primeira_retorna_veredicto_com_tipo() -> None:
    leitor = LeitorDeBytesFalso(conteudo_do_blob=b"%PDF-1.4")
    detector = DetectorDeTipoFalso([ResultadoDaDeteccao(tipo=TipoDeArquivo.PDF)])
    caso_de_uso = _criar_caso_de_uso(leitor, detector)

    veredicto = await caso_de_uso.executar(_ENDERECO)

    assert veredicto.tipo_de_arquivo is TipoDeArquivo.PDF
    assert leitor.chamadas == [_JANELA_DE_CABECALHO_EM_BYTES]


async def test_executar_com_tamanho_acima_do_limite_levanta_excede_limite_sem_detectar() -> None:
    leitor = LeitorDeBytesFalso(conteudo_do_blob=b"x" * (_TAMANHO_MAXIMO_EM_BYTES + 1))
    detector = DetectorDeTipoFalso([])

    caso_de_uso = _criar_caso_de_uso(leitor, detector)

    with pytest.raises(ArquivoExcedeLimite):
        await caso_de_uso.executar(_ENDERECO)

    assert detector.bytes_recebidos == []


async def test_executar_com_zip_ambiguo_reampliado_para_docx_retorna_veredicto_docx() -> None:
    leitor = LeitorDeBytesFalso(conteudo_do_blob=b"PK" + b"\x00" * 40)
    detector = DetectorDeTipoFalso(
        [
            ResultadoDaDeteccao(tipo=None, ambiguo=True),
            ResultadoDaDeteccao(tipo=TipoDeArquivo.DOCX),
        ]
    )
    caso_de_uso = _criar_caso_de_uso(leitor, detector)

    veredicto = await caso_de_uso.executar(_ENDERECO)

    assert veredicto.tipo_de_arquivo is TipoDeArquivo.DOCX
    assert leitor.chamadas == [_JANELA_DE_CABECALHO_EM_BYTES, _JANELA_AMPLIADA_EM_BYTES]
    assert len(detector.bytes_recebidos) == 2


async def test_executar_com_zip_ainda_ambiguo_apos_reampliar_levanta_tipo_nao_suportado() -> None:
    leitor = LeitorDeBytesFalso(conteudo_do_blob=b"PK" + b"\x00" * 40)
    detector = DetectorDeTipoFalso(
        [
            ResultadoDaDeteccao(tipo=None, ambiguo=True),
            ResultadoDaDeteccao(tipo=None, ambiguo=True),
        ]
    )
    caso_de_uso = _criar_caso_de_uso(leitor, detector)

    with pytest.raises(TipoDeArquivoNaoSuportado):
        await caso_de_uso.executar(_ENDERECO)


async def test_executar_com_tipo_nao_suportado_sem_ambiguidade_levanta_tipo_nao_suportado() -> None:
    leitor = LeitorDeBytesFalso(conteudo_do_blob=b"\x7fELF")
    detector = DetectorDeTipoFalso([ResultadoDaDeteccao(tipo=None)])
    caso_de_uso = _criar_caso_de_uso(leitor, detector)

    with pytest.raises(TipoDeArquivoNaoSuportado):
        await caso_de_uso.executar(_ENDERECO)


async def test_executar_com_blob_inacessivel_propaga_documento_inacessivel() -> None:
    caso_de_uso = _criar_caso_de_uso(LeitorDeBytesQueFalha(), DetectorDeTipoFalso([]))

    with pytest.raises(DocumentoInacessivel):
        await caso_de_uso.executar(_ENDERECO)
