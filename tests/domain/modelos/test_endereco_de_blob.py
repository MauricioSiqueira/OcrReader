"""Testes do value object `EnderecoDeBlob`."""

from __future__ import annotations

import pytest

from ocr_reader.domain.erros import EnderecoInvalido
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob

_HOSTS_PERMITIDOS = ["*.blob.core.windows.net"]
_URI_VALIDO = "https://conta.blob.core.windows.net/container/arquivo.pdf?sv=2024-11-04&sig=abc"


def test_endereco_de_blob_criar_com_uri_valido_retorna_instancia() -> None:
    endereco = EnderecoDeBlob.criar(_URI_VALIDO, _HOSTS_PERMITIDOS)

    assert endereco.uri == _URI_VALIDO


def test_endereco_de_blob_criar_com_esquema_http_levanta_endereco_invalido() -> None:
    uri_http = _URI_VALIDO.replace("https://", "http://")

    with pytest.raises(EnderecoInvalido):
        EnderecoDeBlob.criar(uri_http, _HOSTS_PERMITIDOS)


@pytest.mark.parametrize(
    "uri_com_host_fora_da_allowlist",
    [
        "https://malicioso.com/arquivo.pdf?sig=abc",
        "https://blob.core.windows.net/container/arquivo.pdf?sig=abc",
        "https://conta.blob.core.windows.net.malicioso.com/arquivo.pdf?sig=abc",
    ],
)
def test_endereco_de_blob_criar_com_host_fora_da_allowlist_levanta_endereco_invalido(
    uri_com_host_fora_da_allowlist: str,
) -> None:
    with pytest.raises(EnderecoInvalido):
        EnderecoDeBlob.criar(uri_com_host_fora_da_allowlist, _HOSTS_PERMITIDOS)


def test_endereco_de_blob_criar_sem_query_de_assinatura_levanta_endereco_invalido() -> None:
    uri_sem_query = "https://conta.blob.core.windows.net/container/arquivo.pdf"

    with pytest.raises(EnderecoInvalido):
        EnderecoDeBlob.criar(uri_sem_query, _HOSTS_PERMITIDOS)


def test_endereco_de_blob_criar_com_host_exato_da_allowlist_retorna_instancia() -> None:
    endereco = EnderecoDeBlob.criar(
        "https://meu-host-exato.exemplo.com/a?sig=abc", ["meu-host-exato.exemplo.com"]
    )

    assert endereco.uri.startswith("https://meu-host-exato.exemplo.com")


def test_endereco_de_blob_repr_oculta_a_query_de_assinatura() -> None:
    endereco = EnderecoDeBlob.criar(_URI_VALIDO, _HOSTS_PERMITIDOS)

    representacao = repr(endereco)

    assert "sig=abc" not in representacao
    assert "sv=2024-11-04" not in representacao
    assert "conta.blob.core.windows.net" in representacao
