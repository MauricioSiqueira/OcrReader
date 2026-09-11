"""Tradução de erros de domínio para respostas HTTP.

Nenhum tratador ecoa o corpo da requisição: as mensagens de exceção de domínio são estáticas e
nunca contêm o SAS URI, então repassá-las na resposta é seguro.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ocr_reader.domain.erros import (
    ArquivoExcedeLimite,
    DocumentoInacessivel,
    EnderecoInvalido,
    TipoDeArquivoNaoSuportado,
)

_MAPA_DE_STATUS_POR_ERRO: dict[type[Exception], int] = {
    EnderecoInvalido: status.HTTP_400_BAD_REQUEST,
    TipoDeArquivoNaoSuportado: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ArquivoExcedeLimite: status.HTTP_413_CONTENT_TOO_LARGE,
    DocumentoInacessivel: status.HTTP_502_BAD_GATEWAY,
}


def registrar_tratadores_de_erro(app: FastAPI) -> None:
    """Registra na aplicação FastAPI o tradutor de cada exceção de domínio prevista."""
    for tipo_de_erro, status_http in _MAPA_DE_STATUS_POR_ERRO.items():
        app.add_exception_handler(tipo_de_erro, _criar_tratador(status_http))


def _criar_tratador(
    status_http: int,
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    """Cria um tratador que traduz qualquer exceção para o `status_http` informado."""

    async def tratador(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_http, content={"detalhe": str(exc)})

    return tratador
