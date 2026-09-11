"""DTOs (schemas) da API HTTP."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo


class SolicitacaoDeExtracaoDTO(BaseModel):
    """Corpo da requisição `POST /extracoes`."""

    model_config = ConfigDict(populate_by_name=True)

    sas_uri: str = Field(alias="sasUri")


class RespostaDeValidacaoDTO(BaseModel):
    """Corpo da resposta de sucesso da validação do documento remoto."""

    model_config = ConfigDict(populate_by_name=True)

    tipo_de_arquivo: TipoDeArquivo = Field(alias="tipoDeArquivo")


class ErroDTO(BaseModel):
    """Corpo padrão de resposta de erro."""

    detalhe: str
