"""Testes da rota `GET /health`."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ocr_reader.interfaces.api.aplicacao import criar_aplicacao


def test_get_health_retorna_200_com_situacao_ok() -> None:
    with TestClient(criar_aplicacao()) as cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "ok"}


def test_get_health_responde_200_mesmo_com_configuracao_do_azure_vazia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Nenhum endpoint nem chave configurados: a rota não pode depender do Azure para responder.
    monkeypatch.delenv("OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE", raising=False)
    monkeypatch.delenv("OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE", raising=False)

    with TestClient(criar_aplicacao()) as cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "ok"}
