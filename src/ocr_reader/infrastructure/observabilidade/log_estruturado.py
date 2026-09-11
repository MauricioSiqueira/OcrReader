"""Log estruturado: uma linha JSON por evento no stdout, sem dependência nova.

`logging.Formatter` da biblioteca padrão já é suficiente para emitir um dicionário como JSON —
trazer `structlog` ou `python-json-logger` para isso seria complexidade acidental.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

NOME_DO_LOGGER = "ocr_reader"

_CAMPOS_PADRAO_DO_REGISTRO = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys())


class FormatadorJson(logging.Formatter):
    """Formata cada `LogRecord` como uma única linha JSON.

    Os campos passados via `logger.info(..., extra={...})` entram no JSON; os atributos internos
    do `LogRecord` (nome do logger, número de linha, thread etc.) não.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Serializa o registro como uma linha JSON."""
        corpo: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "nivel": record.levelname,
            "mensagem": record.getMessage(),
        }
        corpo.update(_campos_extras_de(record))
        return json.dumps(corpo, default=str, ensure_ascii=False)


def _campos_extras_de(record: logging.LogRecord) -> dict[str, Any]:
    """Extrai do registro apenas os campos passados via `extra=`, descartando os internos."""
    return {
        chave: valor
        for chave, valor in vars(record).items()
        if chave not in _CAMPOS_PADRAO_DO_REGISTRO
    }


def configurar_log() -> None:
    """Configura o logger da aplicação para emitir uma linha JSON por evento no stdout.

    Substitui os manipuladores existentes em vez de acrescentar: seguro para ser chamada mais de
    uma vez (por exemplo, uma nova instância da aplicação a cada teste) sem duplicar linhas.
    """
    manipulador = logging.StreamHandler(sys.stdout)
    manipulador.setFormatter(FormatadorJson())

    logger = logging.getLogger(NOME_DO_LOGGER)
    logger.handlers = [manipulador]
    logger.setLevel(logging.INFO)
