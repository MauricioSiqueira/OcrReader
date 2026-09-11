"""Modelos do domínio de extração de texto via OCR."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, slots=True)
class IdentificadorDaExtracao:
    """Identificador de uma extração para consulta posterior.

    Attributes:
        valor: O `operation_id` do Azure Document Intelligence.
    """

    valor: str


class SituacaoDaExtracao(Enum):
    """Situação de uma extração de texto solicitada ao serviço de OCR."""

    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"


@dataclass(frozen=True, slots=True)
class ResultadoDaExtracao:
    """Resultado de uma consulta de extração de texto.

    Attributes:
        situacao: Situação atual da extração.
        texto: Texto extraído, presente apenas quando `situacao` é `CONCLUIDA`.
    """

    situacao: SituacaoDaExtracao
    texto: str | None = None
