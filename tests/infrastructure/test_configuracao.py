"""Testes de `Configuracao`: leitura de `.env`, precedência do ambiente real e não vazamento.

Nenhum teste aqui usa o `.env` do repositório — cada um cria o seu em `tmp_path` e troca o
diretório de trabalho com `monkeypatch.chdir`, já que o `env_file` é resolvido relativo ao
diretório de trabalho do processo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ocr_reader.infrastructure.configuracao import (
    HOSTS_PERMITIDOS_PADRAO,
    TAMANHO_MAXIMO_PADRAO_EM_BYTES,
    TIMEOUT_PADRAO_EM_SEGUNDOS,
    Configuracao,
)

_CHAVE_DE_TESTE = "minha-chave-super-secreta"


def test_configuracao_le_valores_do_arquivo_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE", raising=False)
    (tmp_path / ".env").write_text(
        "OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE=https://exemplo.cognitiveservices.azure.com\n"
    )

    configuracao = Configuracao()

    assert (
        configuracao.endpoint_do_document_intelligence
        == "https://exemplo.cognitiveservices.azure.com"
    )


def test_configuracao_variavel_de_ambiente_real_sobrescreve_arquivo_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OCR_READER_TIMEOUT_EM_SEGUNDOS=99\n")
    monkeypatch.setenv("OCR_READER_TIMEOUT_EM_SEGUNDOS", "5")

    configuracao = Configuracao()

    assert configuracao.timeout_em_segundos == 5.0


def test_configuracao_sem_arquivo_env_mantem_padroes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OCR_READER_TIMEOUT_EM_SEGUNDOS", raising=False)
    monkeypatch.delenv("OCR_READER_TAMANHO_MAXIMO_EM_BYTES", raising=False)
    monkeypatch.delenv("OCR_READER_HOSTS_PERMITIDOS", raising=False)

    configuracao = Configuracao()

    assert configuracao.timeout_em_segundos == TIMEOUT_PADRAO_EM_SEGUNDOS
    assert configuracao.tamanho_maximo_em_bytes == TAMANHO_MAXIMO_PADRAO_EM_BYTES
    assert configuracao.hosts_permitidos == list(HOSTS_PERMITIDOS_PADRAO)


def test_configuracao_repr_e_str_nao_revelam_a_chave_lida_do_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE={_CHAVE_DE_TESTE}\n")

    configuracao = Configuracao()

    assert configuracao.chave_do_document_intelligence.get_secret_value() == _CHAVE_DE_TESTE
    assert _CHAVE_DE_TESTE not in repr(configuracao)
    assert _CHAVE_DE_TESTE not in str(configuracao)
