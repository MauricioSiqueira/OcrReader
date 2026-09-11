"""Adaptador do serviço de OCR via Azure Document Intelligence.

## Ponto em aberto resolvido: como consultar o resultado por `result_id`

O SDK (`azure-ai-documentintelligence` 1.0.2) não expõe um método público para buscar o JSON do
resultado por `result_id` — só `get_analyze_result_pdf` e `get_analyze_result_figure`, que servem
para outra coisa. Restavam duas saídas:

1. `poller.continuation_token()` na submissão e retomada por `continuation_token=` na consulta.
2. `GET` direto no endpoint REST documentado, com o cliente autenticado.

Testado empiricamente (submissão + consulta contra um servidor `aiohttp` local, sem Azure real):
o `continuation_token` embute a requisição **e** a resposta inteiras da submissão original (URL,
headers, corpo do 202) codificadas em base64 — não é derivável só do `operation_id`. Usá-lo
exigiria guardar esse token em algum lugar entre o `POST` e o `GET`, o que reintroduz o estado que
o desenho recusa (`plan-0001`, "a API fica sem estado"; o id devolvido ao cliente é o
`operation_id`, não um token maior). A saída 1 foi descartada por isso, não por não funcionar.

A saída 2 foi implementada via `client.send_request` (protocol method do próprio SDK) em vez de um
`httpx` avulso: o cliente assíncrono já injetado reaproveita seu pipeline autenticado — o header
`Ocp-Apim-Subscription-Key` é adicionado automaticamente pela `AzureKeyCredential` configurada no
cliente, sem montar credencial à mão aqui. Confirmado com o mesmo servidor de teste local.
"""

from __future__ import annotations

from typing import Any

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.exceptions import AzureError
from azure.core.rest import HttpRequest

from ocr_reader.domain.erros import ExtracaoNaoEncontrada, ServicoDeOcrIndisponivel
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import (
    IdentificadorDaExtracao,
    ResultadoDaExtracao,
    SituacaoDaExtracao,
)

_CHAVE_DO_OPERATION_ID = "operation_id"
_SITUACOES_EM_PROCESSAMENTO = frozenset({"notStarted", "running"})
_SITUACAO_CONCLUIDA = "succeeded"
_SITUACAO_FALHOU = "failed"


class ServicoDeOcrDocumentIntelligence:
    """Solicita e consulta extração de texto via Azure Document Intelligence (`prebuilt-read`).

    O `DocumentIntelligenceClient` assíncrono é injetado: quem o constrói decide credencial,
    endpoint e ciclo de vida.
    """

    def __init__(
        self, cliente: DocumentIntelligenceClient, id_do_modelo: str, versao_da_api: str
    ) -> None:
        self._cliente = cliente
        self._id_do_modelo = id_do_modelo
        self._versao_da_api = versao_da_api

    async def solicitar_leitura(self, endereco: EnderecoDeBlob) -> IdentificadorDaExtracao:
        """Submete o documento remoto ao serviço de OCR e devolve o identificador da extração.

        Args:
            endereco: Endereço já validado do documento remoto.

        Returns:
            Identificador da extração (`operation_id` do Azure).

        Raises:
            ServicoDeOcrIndisponivel: se a submissão falhar ou não devolver um `operation_id`.
        """
        try:
            poller = await self._cliente.begin_analyze_document(
                self._id_do_modelo, AnalyzeDocumentRequest(url_source=endereco.uri)
            )
        except AzureError:
            raise ServicoDeOcrIndisponivel(
                "Não foi possível solicitar a extração ao serviço de OCR."
            ) from None

        operation_id = poller.details.get(_CHAVE_DO_OPERATION_ID)
        if not operation_id:
            raise ServicoDeOcrIndisponivel(
                "O serviço de OCR não devolveu um identificador de operação."
            )
        return IdentificadorDaExtracao(valor=operation_id)

    async def obter_leitura(self, identificador: IdentificadorDaExtracao) -> ResultadoDaExtracao:
        """Consulta o resultado atual de uma extração via `GET` direto no endpoint REST.

        Args:
            identificador: Identificador devolvido por `solicitar_leitura`.

        Returns:
            O resultado atual da extração.

        Raises:
            ExtracaoNaoEncontrada: se o Azure não reconhece o identificador (`404`).
            ServicoDeOcrIndisponivel: se a consulta falhar ou devolver um erro inesperado.
        """
        requisicao = HttpRequest(
            "GET",
            f"/documentModels/{self._id_do_modelo}/analyzeResults/{identificador.valor}",
            params={"api-version": self._versao_da_api},
        )
        try:
            resposta = await self._cliente.send_request(requisicao)
        except AzureError:
            raise ServicoDeOcrIndisponivel(
                "Não foi possível consultar o resultado no serviço de OCR."
            ) from None

        if resposta.status_code == 404:
            raise ExtracaoNaoEncontrada("Não existe extração com o identificador informado.")
        if resposta.status_code >= 400:
            raise ServicoDeOcrIndisponivel("O serviço de OCR retornou erro na consulta.")

        return _resultado_a_partir_do_corpo(resposta.json())


def _resultado_a_partir_do_corpo(corpo: dict[str, Any]) -> ResultadoDaExtracao:
    """Traduz o corpo JSON de `analyzeResults` para o `ResultadoDaExtracao` do domínio."""
    situacao = corpo.get("status")

    if situacao in _SITUACOES_EM_PROCESSAMENTO:
        return ResultadoDaExtracao(situacao=SituacaoDaExtracao.PROCESSANDO)

    if situacao == _SITUACAO_CONCLUIDA:
        texto = corpo.get("analyzeResult", {}).get("content", "")
        return ResultadoDaExtracao(situacao=SituacaoDaExtracao.CONCLUIDA, texto=texto)

    if situacao == _SITUACAO_FALHOU:
        return ResultadoDaExtracao(situacao=SituacaoDaExtracao.FALHOU)

    raise ServicoDeOcrIndisponivel("O serviço de OCR devolveu uma situação desconhecida.")
