"""Porta para o serviço de OCR que extrai texto de um documento remoto."""

from __future__ import annotations

from typing import Protocol

from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import IdentificadorDaExtracao, ResultadoDaExtracao


class ServicoDeOcr(Protocol):
    """Porta para solicitar e consultar a extração de texto de um documento remoto."""

    async def solicitar_leitura(self, endereco: EnderecoDeBlob) -> IdentificadorDaExtracao:
        """Solicita ao serviço de OCR a leitura do documento no endereço informado.

        Args:
            endereco: Endereço já validado do documento remoto.

        Returns:
            Identificador da extração, usado depois para consultar o resultado.

        Raises:
            ServicoDeOcrIndisponivel: se a submissão ao serviço de OCR falhar.
        """
        ...

    async def obter_leitura(self, identificador: IdentificadorDaExtracao) -> ResultadoDaExtracao:
        """Consulta o resultado de uma extração de texto previamente solicitada.

        Args:
            identificador: Identificador devolvido por `solicitar_leitura`.

        Returns:
            O resultado atual da extração (processando, concluída ou falhou).

        Raises:
            ExtracaoNaoEncontrada: se o identificador não corresponde a uma extração conhecida
                pelo serviço de OCR.
            ServicoDeOcrIndisponivel: se a consulta ao serviço de OCR falhar.
        """
        ...
