"""Adaptador HTTP para leitura de uma janela de bytes de um blob remoto."""

from __future__ import annotations

import httpx

from ocr_reader.domain.erros import DocumentoInacessivel
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.portas.leitor_de_bytes_remotos import CabecalhoRemoto

_CABECALHO_RANGE = "Range"
_CABECALHO_CONTENT_RANGE = "Content-Range"


class LeitorDeBytesHttpx:
    """Lê uma janela inicial de bytes de um blob remoto via `Range` HTTP, usando `httpx`.

    O `httpx.AsyncClient` é injetado: quem o constrói decide timeout e ciclo de vida.
    """

    def __init__(self, cliente_http: httpx.AsyncClient) -> None:
        self._cliente_http = cliente_http

    async def ler_janela(
        self, endereco: EnderecoDeBlob, tamanho_da_janela_em_bytes: int
    ) -> CabecalhoRemoto:
        """Lê os primeiros `tamanho_da_janela_em_bytes` bytes do blob e seu tamanho total.

        Args:
            endereco: Endereço já validado do blob remoto.
            tamanho_da_janela_em_bytes: Quantidade de bytes a ler a partir do início.

        Returns:
            O cabeçalho lido e o tamanho total do recurso, extraído do `Content-Range`.

        Raises:
            DocumentoInacessivel: se a requisição falhar ou o `Content-Range` não vier na
                resposta. A causa original nunca é encadeada, para que o SAS URI da requisição
                jamais apareça em um traceback.
        """
        cabecalhos = {_CABECALHO_RANGE: f"bytes=0-{tamanho_da_janela_em_bytes - 1}"}

        try:
            resposta = await self._cliente_http.get(endereco.uri, headers=cabecalhos)
        except httpx.HTTPError:
            raise DocumentoInacessivel("Não foi possível acessar o documento remoto.") from None

        if resposta.status_code >= httpx.codes.BAD_REQUEST:
            raise DocumentoInacessivel("O documento remoto retornou erro de acesso.")

        tamanho_total = _extrair_tamanho_total(resposta.headers.get(_CABECALHO_CONTENT_RANGE))
        return CabecalhoRemoto(bytes_lidos=resposta.content, tamanho_total_em_bytes=tamanho_total)


def _extrair_tamanho_total(content_range: str | None) -> int:
    """Extrai o tamanho total de um cabeçalho `Content-Range` no formato `bytes 0-N/total`."""
    if content_range is None or "/" not in content_range:
        raise DocumentoInacessivel(
            "O documento remoto não informou o tamanho total (Content-Range)."
        )

    total = content_range.rsplit("/", maxsplit=1)[-1]
    try:
        return int(total)
    except ValueError:
        raise DocumentoInacessivel("Content-Range do documento remoto é inválido.") from None
