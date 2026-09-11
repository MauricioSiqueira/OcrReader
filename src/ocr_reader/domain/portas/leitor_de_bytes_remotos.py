"""Porta para leitura de uma janela de bytes do início de um recurso remoto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob


@dataclass(frozen=True, slots=True)
class CabecalhoRemoto:
    """Janela inicial de bytes de um recurso remoto e seu tamanho total.

    Attributes:
        bytes_lidos: Primeiros bytes do recurso, limitados à janela requisitada.
        tamanho_total_em_bytes: Tamanho total do recurso no servidor, extraído do header
            `Content-Range`.
    """

    bytes_lidos: bytes
    tamanho_total_em_bytes: int


class LeitorDeBytesRemotos(Protocol):
    """Porta para ler uma janela de bytes do início de um recurso remoto, sem baixá-lo inteiro."""

    async def ler_janela(
        self, endereco: EnderecoDeBlob, tamanho_da_janela_em_bytes: int
    ) -> CabecalhoRemoto:
        """Lê os primeiros `tamanho_da_janela_em_bytes` bytes do recurso e seu tamanho total.

        Args:
            endereco: Endereço já validado do blob remoto.
            tamanho_da_janela_em_bytes: Quantidade de bytes a ler a partir do início.

        Returns:
            O cabeçalho lido e o tamanho total do recurso.

        Raises:
            DocumentoInacessivel: se o recurso não pôde ser lido (rede, autorização, SAS expirado).
        """
        ...
