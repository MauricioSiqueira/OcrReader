"""Configuração da API via variáveis de ambiente."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_UM_KIBIBYTE_EM_BYTES = 1024
_UM_MEBIBYTE_EM_BYTES = 1024 * _UM_KIBIBYTE_EM_BYTES

TAMANHO_MAXIMO_PADRAO_EM_BYTES = 500 * _UM_MEBIBYTE_EM_BYTES
JANELA_DE_CABECALHO_PADRAO_EM_BYTES = 8 * _UM_KIBIBYTE_EM_BYTES
JANELA_AMPLIADA_PADRAO_EM_BYTES = 512 * _UM_KIBIBYTE_EM_BYTES
TIMEOUT_PADRAO_EM_SEGUNDOS = 10.0
HOSTS_PERMITIDOS_PADRAO = ("*.blob.core.windows.net",)


class Configuracao(BaseSettings):
    """Configuração operacional da validação de documento remoto.

    Cada campo pode ser sobrescrito por variável de ambiente com prefixo `OCR_READER_`
    (ex.: `OCR_READER_TAMANHO_MAXIMO_EM_BYTES`).
    """

    model_config = SettingsConfigDict(env_prefix="OCR_READER_")

    hosts_permitidos: list[str] = Field(default_factory=lambda: list(HOSTS_PERMITIDOS_PADRAO))
    tamanho_maximo_em_bytes: int = TAMANHO_MAXIMO_PADRAO_EM_BYTES
    janela_de_cabecalho_em_bytes: int = JANELA_DE_CABECALHO_PADRAO_EM_BYTES
    janela_ampliada_em_bytes: int = JANELA_AMPLIADA_PADRAO_EM_BYTES
    timeout_em_segundos: float = TIMEOUT_PADRAO_EM_SEGUNDOS
