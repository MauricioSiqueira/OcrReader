"""DTOs (schemas) da API HTTP."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ocr_reader.domain.modelos.extracao import SituacaoDaExtracao


class SolicitacaoDeExtracaoDTO(BaseModel):
    """Corpo da requisição `POST /extracoes`."""

    model_config = ConfigDict(populate_by_name=True)

    sas_uri: str = Field(alias="sasUri")


class RespostaDeSolicitacaoDTO(BaseModel):
    """Corpo da resposta de aceite da solicitação de extração (`202`)."""

    model_config = ConfigDict(populate_by_name=True)

    id_extracao: str = Field(alias="idExtracao")
    situacao: SituacaoDaExtracao


class RespostaDeConsultaDTO(BaseModel):
    """Corpo da resposta de consulta de uma extração: `200` quando concluída, `202` em processo."""

    situacao: SituacaoDaExtracao
    texto: str | None = None


class ErroDTO(BaseModel):
    """Corpo padrão de resposta de erro."""

    detalhe: str


class RespostaDeSaudeDTO(BaseModel):
    """Corpo da resposta de `GET /health`."""

    situacao: str = "ok"
