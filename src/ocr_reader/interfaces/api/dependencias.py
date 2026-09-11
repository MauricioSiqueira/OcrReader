"""Injeção de dependências da camada de interface HTTP."""

from __future__ import annotations

from fastapi import Request

from ocr_reader.application.casos_de_uso.consultar_extracao_de_texto import (
    ConsultarExtracaoDeTexto,
)
from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import (
    SolicitarExtracaoDeTexto,
)
from ocr_reader.infrastructure.configuracao import Configuracao


def obter_configuracao(request: Request) -> Configuracao:
    """Recupera a configuração da aplicação armazenada no estado do FastAPI."""
    configuracao: Configuracao = request.app.state.configuracao
    return configuracao


def obter_caso_de_uso_de_solicitacao(request: Request) -> SolicitarExtracaoDeTexto:
    """Recupera o caso de uso de solicitação de extração armazenado no estado do FastAPI."""
    caso_de_uso: SolicitarExtracaoDeTexto = request.app.state.caso_de_uso_de_solicitacao
    return caso_de_uso


def obter_caso_de_uso_de_consulta(request: Request) -> ConsultarExtracaoDeTexto:
    """Recupera o caso de uso de consulta de extração armazenado no estado do FastAPI."""
    caso_de_uso: ConsultarExtracaoDeTexto = request.app.state.caso_de_uso_de_consulta
    return caso_de_uso
