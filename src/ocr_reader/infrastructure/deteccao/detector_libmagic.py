"""Adaptador de detecção de tipo de arquivo via magic bytes (`libmagic`)."""

from __future__ import annotations

import magic

from ocr_reader.domain.modelos.resultado_da_deteccao import ResultadoDaDeteccao
from ocr_reader.domain.modelos.tipo_de_arquivo import (
    MIME_TYPES_ZIP_AMBIGUOS,
    tipo_de_arquivo_a_partir_do_mime,
)


class DetectorLibmagic:
    """Detecta o tipo de arquivo a partir de magic bytes usando `libmagic`."""

    def detectar(self, bytes_lidos: bytes) -> ResultadoDaDeteccao:
        """Detecta o tipo de arquivo a partir da janela de bytes fornecida.

        Args:
            bytes_lidos: Janela de bytes do início do arquivo.

        Returns:
            O veredito da detecção: um `TipoDeArquivo` reconhecido, `None` se não aceito, ou
            sinalização de ambiguidade quando o MIME type é ZIP genérico (possível OOXML).
        """
        mime_type = magic.from_buffer(bytes_lidos, mime=True)

        if mime_type in MIME_TYPES_ZIP_AMBIGUOS:
            return ResultadoDaDeteccao(tipo=None, ambiguo=True)

        return ResultadoDaDeteccao(tipo=tipo_de_arquivo_a_partir_do_mime(mime_type))
