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
class MetricasDaExtracao:
    """Métricas de processamento de uma extração concluída.

    Attributes:
        duracao_do_ocr_em_ms: Duração do processamento no serviço de OCR, em milissegundos.
        quantidade_de_paginas: Número de páginas analisadas.
    """

    duracao_do_ocr_em_ms: int
    quantidade_de_paginas: int


@dataclass(frozen=True, slots=True)
class ResultadoDaExtracao:
    """Resultado de uma consulta de extração de texto.

    Attributes:
        situacao: Situação atual da extração.
        texto: Texto extraído, presente apenas quando `situacao` é `CONCLUIDA`.
        metricas: Métricas de processamento. Presentes apenas quando `situacao` é `CONCLUIDA` e o
            serviço de OCR devolveu os dados necessários para calculá-las; ausência de métricas
            nunca impede a resposta.
    """

    situacao: SituacaoDaExtracao
    texto: str | None = None
    metricas: MetricasDaExtracao | None = None
