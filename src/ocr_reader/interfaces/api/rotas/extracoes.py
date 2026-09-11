"""Rota `POST /extracoes`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from ocr_reader.application.casos_de_uso.validar_documento_remoto import ValidarDocumentoRemoto
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.interfaces.api.dependencias import (
    obter_caso_de_uso_de_validacao,
    obter_configuracao,
)
from ocr_reader.interfaces.api.esquemas import RespostaDeValidacaoDTO, SolicitacaoDeExtracaoDTO

roteador = APIRouter()

_Configuracao = Annotated[Configuracao, Depends(obter_configuracao)]
_CasoDeUsoDeValidacao = Annotated[ValidarDocumentoRemoto, Depends(obter_caso_de_uso_de_validacao)]


@roteador.post(
    "/extracoes",
    response_model=RespostaDeValidacaoDTO,
    status_code=status.HTTP_200_OK,
)
async def validar_documento(
    solicitacao: SolicitacaoDeExtracaoDTO,
    configuracao: _Configuracao,
    caso_de_uso: _CasoDeUsoDeValidacao,
) -> RespostaDeValidacaoDTO:
    """Valida um documento remoto e retorna o tipo de arquivo detectado.

    A validação do endereço (esquema, allowlist de host, presença de assinatura SAS) acontece
    antes de qualquer requisição de rede: um endereço rejeitado nunca chega a ser acessado.
    """
    endereco = EnderecoDeBlob.criar(solicitacao.sas_uri, configuracao.hosts_permitidos)
    veredicto = await caso_de_uso.executar(endereco)
    return RespostaDeValidacaoDTO(tipo_de_arquivo=veredicto.tipo_de_arquivo)
