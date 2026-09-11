"""Caso de uso: consultar o resultado de uma extração de texto solicitada."""

from __future__ import annotations

from ocr_reader.domain.erros import ServicoDeOcrIndisponivel
from ocr_reader.domain.modelos.extracao import (
    IdentificadorDaExtracao,
    ResultadoDaExtracao,
    SituacaoDaExtracao,
)
from ocr_reader.domain.portas.servico_de_ocr import ServicoDeOcr


class ConsultarExtracaoDeTexto:
    """Consulta o serviço de OCR pelo resultado atual de uma extração.

    Trata uma extração que falhou no Azure como indisponibilidade do serviço: do ponto de vista
    do consumidor da nossa API, ambas viram `502`. Essa tradução é uma decisão de negócio, por
    isso vive aqui e não no adaptador nem na rota.
    """

    def __init__(self, servico_de_ocr: ServicoDeOcr) -> None:
        self._servico_de_ocr = servico_de_ocr

    async def executar(self, identificador: IdentificadorDaExtracao) -> ResultadoDaExtracao:
        """Consulta o resultado atual da extração.

        Args:
            identificador: Identificador da extração a consultar.

        Returns:
            O resultado atual: processando ou concluída (com texto).

        Raises:
            ExtracaoNaoEncontrada: se o identificador não corresponde a uma extração conhecida.
            ServicoDeOcrIndisponivel: se a consulta falhar ou se a extração tiver falhado no
                serviço de OCR.
        """
        resultado = await self._servico_de_ocr.obter_leitura(identificador)
        if resultado.situacao is SituacaoDaExtracao.FALHOU:
            raise ServicoDeOcrIndisponivel("A extração de texto falhou no serviço de OCR.")
        return resultado
