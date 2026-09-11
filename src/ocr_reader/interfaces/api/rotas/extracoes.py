"""Rotas `POST /extracoes` e `GET /extracoes/{id_extracao}`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from ocr_reader.application.casos_de_uso.consultar_extracao_de_texto import (
    ConsultarExtracaoDeTexto,
)
from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import (
    SolicitarExtracaoDeTexto,
)
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import IdentificadorDaExtracao, SituacaoDaExtracao
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.interfaces.api.dependencias import (
    obter_caso_de_uso_de_consulta,
    obter_caso_de_uso_de_solicitacao,
    obter_configuracao,
)
from ocr_reader.interfaces.api.esquemas import (
    RespostaDeConsultaDTO,
    RespostaDeSolicitacaoDTO,
    SolicitacaoDeExtracaoDTO,
)

roteador = APIRouter()

_Configuracao = Annotated[Configuracao, Depends(obter_configuracao)]
_CasoDeUsoDeSolicitacao = Annotated[
    SolicitarExtracaoDeTexto, Depends(obter_caso_de_uso_de_solicitacao)
]
_CasoDeUsoDeConsulta = Annotated[ConsultarExtracaoDeTexto, Depends(obter_caso_de_uso_de_consulta)]

_CAMINHO_DE_CONSULTA = "/extracoes/{id_extracao}"


@roteador.post(
    "/extracoes",
    response_model=RespostaDeSolicitacaoDTO,
    status_code=status.HTTP_202_ACCEPTED,
)
async def solicitar_extracao(
    solicitacao: SolicitacaoDeExtracaoDTO,
    configuracao: _Configuracao,
    caso_de_uso: _CasoDeUsoDeSolicitacao,
    response: Response,
) -> RespostaDeSolicitacaoDTO:
    """Valida o documento remoto e solicita sua extração de texto ao serviço de OCR.

    A validação (esquema, allowlist de host, assinatura SAS, tipo de arquivo, tamanho) acontece
    antes de qualquer chamada ao serviço de OCR: uma rejeição nunca chega a acioná-lo.
    """
    endereco = EnderecoDeBlob.criar(solicitacao.sas_uri, configuracao.hosts_permitidos)
    extracao_solicitada = await caso_de_uso.executar(endereco)

    response.headers["Location"] = _CAMINHO_DE_CONSULTA.format(
        id_extracao=extracao_solicitada.identificador.valor
    )
    return RespostaDeSolicitacaoDTO(
        id_extracao=extracao_solicitada.identificador.valor,
        situacao=SituacaoDaExtracao.PROCESSANDO,
    )


@roteador.get(_CAMINHO_DE_CONSULTA, response_model=RespostaDeConsultaDTO)
async def consultar_extracao(
    id_extracao: str,
    caso_de_uso: _CasoDeUsoDeConsulta,
    response: Response,
) -> RespostaDeConsultaDTO:
    """Consulta o resultado de uma extração de texto previamente solicitada."""
    resultado = await caso_de_uso.executar(IdentificadorDaExtracao(valor=id_extracao))

    response.status_code = (
        status.HTTP_200_OK
        if resultado.situacao is SituacaoDaExtracao.CONCLUIDA
        else status.HTTP_202_ACCEPTED
    )
    return RespostaDeConsultaDTO(situacao=resultado.situacao, texto=resultado.texto)
