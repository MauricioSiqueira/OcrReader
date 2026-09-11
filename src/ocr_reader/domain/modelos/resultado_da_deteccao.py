"""Resultado da detecção de tipo de arquivo a partir de uma janela de bytes."""

from __future__ import annotations

from dataclasses import dataclass

from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo


@dataclass(frozen=True, slots=True)
class ResultadoDaDeteccao:
    """Veredito de uma tentativa de detecção de tipo de arquivo.

    `tipo` vem preenchido quando a janela de bytes foi suficiente para reconhecer um tipo aceito.
    `ambiguo` sinaliza que o formato encontrado (ex.: ZIP genérico) pode ser um contêiner OOXML
    (DOCX/XLSX/PPTX) que exige uma janela maior de bytes para ser distinguido de um ZIP comum.
    """

    tipo: TipoDeArquivo | None
    ambiguo: bool = False
