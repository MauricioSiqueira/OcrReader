"""Testes de `FormatadorJson` e `configurar_log`."""

from __future__ import annotations

import json
import logging
import sys

from ocr_reader.infrastructure.observabilidade.log_estruturado import (
    NOME_DO_LOGGER,
    FormatadorJson,
    configurar_log,
)


def _criar_registro(mensagem: str, **extra: object) -> logging.LogRecord:
    registro = logging.LogRecord(
        name="teste",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=mensagem,
        args=(),
        exc_info=None,
    )
    for chave, valor in extra.items():
        setattr(registro, chave, valor)
    return registro


def test_formatador_json_produz_json_valido_com_campos_padrao() -> None:
    registro = _criar_registro("evento_de_teste")

    corpo = json.loads(FormatadorJson().format(registro))

    assert corpo["mensagem"] == "evento_de_teste"
    assert corpo["nivel"] == "INFO"
    assert "timestamp" in corpo


def test_formatador_json_inclui_campos_extras_e_exclui_atributos_internos() -> None:
    registro = _criar_registro("evento_de_teste", evento="extracao_solicitada", id_extracao="op-1")

    corpo = json.loads(FormatadorJson().format(registro))

    assert corpo["evento"] == "extracao_solicitada"
    assert corpo["id_extracao"] == "op-1"
    assert "pathname" not in corpo
    assert "lineno" not in corpo
    assert "levelno" not in corpo


def test_configurar_log_configura_um_unico_handler_stdout_com_formatador_json() -> None:
    configurar_log()
    configurar_log()  # chamar duas vezes não pode duplicar o handler
    logger = logging.getLogger(NOME_DO_LOGGER)

    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, FormatadorJson)
    assert logger.handlers[0].stream is sys.stdout
