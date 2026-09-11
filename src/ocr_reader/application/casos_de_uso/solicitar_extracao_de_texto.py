"""Caso de uso: solicitar a extração de texto de um documento remoto."""

from __future__ import annotations

from dataclasses import dataclass

from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import IdentificadorDaExtracao
from ocr_reader.domain.portas.servico_de_ocr import ServicoDeOcr


@dataclass(frozen=True, slots=True)
class ExtracaoSolicitada:
    """Resultado de uma solicitação de extração aceita.

    Attributes:
        identificador: Identificador da extração, para consulta posterior via
            `ConsultarExtracaoDeTexto`.
    """

    identificador: IdentificadorDaExtracao


class SolicitarExtracaoDeTexto:
    """Valida o documento remoto e, aprovado, solicita a extração de texto ao serviço de OCR.

    Reaproveita `ValidarDocumentoRemoto` por composição: a validação em si (endereço, tamanho,
    tipo de arquivo) não é reimplementada aqui.
    """

    def __init__(
        self, validar_documento_remoto: ValidarDocumentoRemoto, servico_de_ocr: ServicoDeOcr
    ) -> None:
        self._validar_documento_remoto = validar_documento_remoto
        self._servico_de_ocr = servico_de_ocr

    async def executar(self, endereco: EnderecoDeBlob) -> ExtracaoSolicitada:
        """Valida o documento remoto e solicita sua extração de texto.

        Args:
            endereco: Endereço já validado (esquema, allowlist, assinatura) do documento remoto.

        Returns:
            A extração solicitada, com o identificador para consulta posterior.

        Raises:
            ArquivoExcedeLimite: se o tamanho total excede o limite configurado.
            TipoDeArquivoNaoSuportado: se o tipo detectado não é aceito.
            DocumentoInacessivel: se o blob não pôde ser lido.
            ServicoDeOcrIndisponivel: se a submissão ao serviço de OCR falhar.
        """
        await self._validar_documento_remoto.executar(endereco)
        identificador = await self._servico_de_ocr.solicitar_leitura(endereco)
        return ExtracaoSolicitada(identificador=identificador)
