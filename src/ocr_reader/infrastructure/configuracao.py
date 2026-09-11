"""Configuração da API via variáveis de ambiente."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_UM_KIBIBYTE_EM_BYTES = 1024
_UM_MEBIBYTE_EM_BYTES = 1024 * _UM_KIBIBYTE_EM_BYTES

TAMANHO_MAXIMO_PADRAO_EM_BYTES = 500 * _UM_MEBIBYTE_EM_BYTES
JANELA_DE_CABECALHO_PADRAO_EM_BYTES = 8 * _UM_KIBIBYTE_EM_BYTES
JANELA_AMPLIADA_PADRAO_EM_BYTES = 512 * _UM_KIBIBYTE_EM_BYTES
TIMEOUT_PADRAO_EM_SEGUNDOS = 10.0
HOSTS_PERMITIDOS_PADRAO = ("*.blob.core.windows.net",)
ID_DO_MODELO_DE_OCR_PADRAO = "prebuilt-read"
VERSAO_DA_API_DE_OCR_PADRAO = "2024-11-30"


class Configuracao(BaseSettings):
    """Configuração operacional da validação de documento remoto e extração de texto.

    Lê valores em ordem de precedência:
    1. Variáveis de ambiente com prefixo `OCR_READER_` (ex.: `OCR_READER_TAMANHO_MAXIMO_EM_BYTES`)
    2. Arquivo `.env` na raiz do projeto (se existir)
    3. Padrões hardcoded em cada campo

    Variáveis de ambiente **sobrescrevem** valores do `.env`, garantindo que em container ou CI
    a configuração chegue seguramente pelo ambiente sem ser afetada por um arquivo esquecido.
    """

    model_config = SettingsConfigDict(
        env_prefix="OCR_READER_", env_file=".env", env_file_encoding="utf-8"
    )

    hosts_permitidos: list[str] = Field(default_factory=lambda: list(HOSTS_PERMITIDOS_PADRAO))
    tamanho_maximo_em_bytes: int = TAMANHO_MAXIMO_PADRAO_EM_BYTES
    janela_de_cabecalho_em_bytes: int = JANELA_DE_CABECALHO_PADRAO_EM_BYTES
    janela_ampliada_em_bytes: int = JANELA_AMPLIADA_PADRAO_EM_BYTES
    timeout_em_segundos: float = TIMEOUT_PADRAO_EM_SEGUNDOS

    endpoint_do_document_intelligence: str = ""
    chave_do_document_intelligence: SecretStr = SecretStr("")
    id_do_modelo_de_ocr: str = ID_DO_MODELO_DE_OCR_PADRAO
    versao_da_api_de_ocr: str = VERSAO_DA_API_DE_OCR_PADRAO
