"""Test doubles das portas de domínio, para testar aplicação e interfaces sem IO real."""

from __future__ import annotations

from ocr_reader.domain.erros import DocumentoInacessivel
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.resultado_da_deteccao import ResultadoDaDeteccao
from ocr_reader.domain.portas.leitor_de_bytes_remotos import CabecalhoRemoto


class LeitorDeBytesFalso:
    """Simula um blob remoto cujo conteúdo é `conteudo_do_blob`, honrando janelas de leitura."""

    def __init__(self, conteudo_do_blob: bytes) -> None:
        self.conteudo_do_blob = conteudo_do_blob
        self.chamadas: list[int] = []

    async def ler_janela(
        self, endereco: EnderecoDeBlob, tamanho_da_janela_em_bytes: int
    ) -> CabecalhoRemoto:
        self.chamadas.append(tamanho_da_janela_em_bytes)
        janela = self.conteudo_do_blob[:tamanho_da_janela_em_bytes]
        return CabecalhoRemoto(
            bytes_lidos=janela, tamanho_total_em_bytes=len(self.conteudo_do_blob)
        )


class LeitorDeBytesQueFalha:
    """Simula um blob remoto inacessível: toda leitura levanta `DocumentoInacessivel`."""

    async def ler_janela(
        self, endereco: EnderecoDeBlob, tamanho_da_janela_em_bytes: int
    ) -> CabecalhoRemoto:
        raise DocumentoInacessivel("Falha simulada de acesso ao blob remoto.")


class DetectorDeTipoFalso:
    """Retorna resultados de detecção pré-programados, na ordem em que são consultados."""

    def __init__(self, resultados: list[ResultadoDaDeteccao]) -> None:
        self._resultados = list(resultados)
        self.bytes_recebidos: list[bytes] = []

    def detectar(self, bytes_lidos: bytes) -> ResultadoDaDeteccao:
        self.bytes_recebidos.append(bytes_lidos)
        return self._resultados.pop(0)
