"""Testes do adaptador `LeitorDeBytesHttpx`, com transporte `httpx` simulado (sem rede real)."""

from __future__ import annotations

import httpx
import pytest

from ocr_reader.domain.erros import DocumentoInacessivel
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.infrastructure.http.leitor_de_bytes_httpx import LeitorDeBytesHttpx

_ENDERECO = EnderecoDeBlob.criar(
    "https://conta.blob.core.windows.net/container/arquivo.pdf?sig=abc", ["*.blob.core.windows.net"]
)


def _criar_leitor(transporte: httpx.MockTransport) -> LeitorDeBytesHttpx:
    cliente_http = httpx.AsyncClient(transport=transporte)
    return LeitorDeBytesHttpx(cliente_http)


async def test_ler_janela_com_content_range_presente_retorna_cabecalho_e_tamanho_total() -> None:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert requisicao.headers["Range"] == "bytes=0-7"
        return httpx.Response(
            206,
            headers={"Content-Range": "bytes 0-7/123456"},
            content=b"%PDF-1.4",
        )

    leitor = _criar_leitor(httpx.MockTransport(responder))

    cabecalho = await leitor.ler_janela(_ENDERECO, tamanho_da_janela_em_bytes=8)

    assert cabecalho.bytes_lidos == b"%PDF-1.4"
    assert cabecalho.tamanho_total_em_bytes == 123456


async def test_ler_janela_com_status_de_erro_levanta_documento_inacessivel() -> None:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    leitor = _criar_leitor(httpx.MockTransport(responder))

    with pytest.raises(DocumentoInacessivel):
        await leitor.ler_janela(_ENDERECO, tamanho_da_janela_em_bytes=8)


async def test_ler_janela_sem_content_range_levanta_documento_inacessivel() -> None:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"conteudo completo, sem content-range")

    leitor = _criar_leitor(httpx.MockTransport(responder))

    with pytest.raises(DocumentoInacessivel):
        await leitor.ler_janela(_ENDERECO, tamanho_da_janela_em_bytes=8)


async def test_ler_janela_com_erro_de_rede_levanta_documento_inacessivel_sem_causa() -> None:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("falha de conexão simulada")

    leitor = _criar_leitor(httpx.MockTransport(responder))

    with pytest.raises(DocumentoInacessivel) as excecao:
        await leitor.ler_janela(_ENDERECO, tamanho_da_janela_em_bytes=8)

    assert excecao.value.__cause__ is None
