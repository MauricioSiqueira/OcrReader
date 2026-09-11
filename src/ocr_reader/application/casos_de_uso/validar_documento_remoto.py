"""Caso de uso: validar um documento remoto a partir do seu endereço."""

from __future__ import annotations

from dataclasses import dataclass

from ocr_reader.domain.erros import ArquivoExcedeLimite, TipoDeArquivoNaoSuportado
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from ocr_reader.domain.portas.detector_de_tipo_de_arquivo import DetectorDeTipoDeArquivo
from ocr_reader.domain.portas.leitor_de_bytes_remotos import LeitorDeBytesRemotos


@dataclass(frozen=True, slots=True)
class VeredictoDeValidacao:
    """Resultado da validação bem-sucedida de um documento remoto.

    Attributes:
        tipo_de_arquivo: Tipo de arquivo detectado no blob, garantido estar entre os
            aceitos pela API.
    """

    tipo_de_arquivo: TipoDeArquivo


class ValidarDocumentoRemoto:
    """Orquestra a validação de um documento remoto: endereço, cabeçalho, detecção e veredito."""

    def __init__(
        self,
        leitor_de_bytes: LeitorDeBytesRemotos,
        detector_de_tipo: DetectorDeTipoDeArquivo,
        tamanho_maximo_em_bytes: int,
        janela_de_cabecalho_em_bytes: int,
        janela_ampliada_em_bytes: int,
    ) -> None:
        self._leitor_de_bytes = leitor_de_bytes
        self._detector_de_tipo = detector_de_tipo
        self._tamanho_maximo_em_bytes = tamanho_maximo_em_bytes
        self._janela_de_cabecalho_em_bytes = janela_de_cabecalho_em_bytes
        self._janela_ampliada_em_bytes = janela_ampliada_em_bytes

    async def executar(self, endereco: EnderecoDeBlob) -> VeredictoDeValidacao:
        """Valida o documento remoto e retorna o veredito.

        Args:
            endereco: Endereço já validado do blob remoto.

        Returns:
            O veredito com o tipo de arquivo detectado.

        Raises:
            ArquivoExcedeLimite: se o tamanho total excede o limite configurado.
            TipoDeArquivoNaoSuportado: se o tipo detectado não é aceito.
            DocumentoInacessivel: se o blob não pôde ser lido.
        """
        cabecalho = await self._leitor_de_bytes.ler_janela(
            endereco, self._janela_de_cabecalho_em_bytes
        )
        self._verificar_tamanho(cabecalho.tamanho_total_em_bytes)

        tipo_de_arquivo = await self._detectar_tipo(endereco, cabecalho.bytes_lidos)
        if tipo_de_arquivo is None:
            raise TipoDeArquivoNaoSuportado("Tipo de arquivo não está entre os aceitos.")

        return VeredictoDeValidacao(tipo_de_arquivo=tipo_de_arquivo)

    def _verificar_tamanho(self, tamanho_total_em_bytes: int) -> None:
        """Levanta `ArquivoExcedeLimite` se o tamanho total ultrapassa o limite configurado."""
        if tamanho_total_em_bytes > self._tamanho_maximo_em_bytes:
            raise ArquivoExcedeLimite("Arquivo excede o tamanho máximo configurado.")

    async def _detectar_tipo(
        self, endereco: EnderecoDeBlob, bytes_do_cabecalho: bytes
    ) -> TipoDeArquivo | None:
        """Detecta o tipo a partir do cabeçalho, reampliando a janela uma única vez se ambíguo."""
        resultado = self._detector_de_tipo.detectar(bytes_do_cabecalho)
        if not resultado.ambiguo:
            return resultado.tipo

        cabecalho_ampliado = await self._leitor_de_bytes.ler_janela(
            endereco, self._janela_ampliada_em_bytes
        )
        resultado_ampliado = self._detector_de_tipo.detectar(cabecalho_ampliado.bytes_lidos)
        return resultado_ampliado.tipo
