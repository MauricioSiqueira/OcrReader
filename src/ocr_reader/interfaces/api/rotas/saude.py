"""Rota `GET /health`."""

from __future__ import annotations

from fastapi import APIRouter

from ocr_reader.interfaces.api.esquemas import RespostaDeSaudeDTO

roteador = APIRouter()


@roteador.get("/health", response_model=RespostaDeSaudeDTO)
async def verificar_saude() -> RespostaDeSaudeDTO:
    """Confirma que o processo está de pé e atendendo requisições.

    Liveness pura: não consulta o serviço de OCR nem qualquer outra dependência externa. Uma
    instabilidade momentânea do Azure nunca deve derrubar um processo que está saudável.
    """
    return RespostaDeSaudeDTO()
