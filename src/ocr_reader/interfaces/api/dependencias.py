"""Injeção de dependências da camada de interface HTTP."""

from __future__ import annotations

from fastapi import Request

from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.infrastructure.configuracao import Configuracao


def obter_configuracao(request: Request) -> Configuracao:
    """Recupera a configuração da aplicação armazenada no estado do FastAPI."""
    configuracao: Configuracao = request.app.state.configuracao
    return configuracao


def obter_caso_de_uso_de_validacao(request: Request) -> ValidarDocumentoRemoto:
    """Recupera o caso de uso de validação de documento remoto armazenado no estado do FastAPI."""
    caso_de_uso: ValidarDocumentoRemoto = request.app.state.caso_de_uso_de_validacao
    return caso_de_uso
