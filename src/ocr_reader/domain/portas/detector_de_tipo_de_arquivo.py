"""Porta para detecção do tipo de arquivo a partir de magic bytes."""

from __future__ import annotations

from typing import Protocol

from ocr_reader.domain.modelos.resultado_da_deteccao import ResultadoDaDeteccao


class DetectorDeTipoDeArquivo(Protocol):
    """Porta para detectar o tipo de arquivo a partir de uma janela de bytes do arquivo."""

    def detectar(self, bytes_lidos: bytes) -> ResultadoDaDeteccao:
        """Detecta o tipo de arquivo a partir dos bytes iniciais fornecidos.

        Args:
            bytes_lidos: Janela de bytes do início do arquivo.

        Returns:
            O veredito da detecção.
        """
        ...
