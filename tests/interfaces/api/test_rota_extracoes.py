"""Testes de integração HTTP das rotas `POST /extracoes` e `GET /extracoes/{id_extracao}`.

Os casos de uso são substituídos por dublês: a orquestração de validação, submissão e consulta já
é coberta pelos testes de `application` e `infrastructure`. Aqui o que se verifica é o
comportamento da camada HTTP — parsing do DTO, código de status por cenário, header `Location`, e
a garantia de que um endereço inválido nunca chega a acionar o serviço de OCR (logo, nunca gera
requisição de rede).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from ocr_reader.application.casos_de_uso.solicitar_extracao_de_texto import ExtracaoSolicitada
from ocr_reader.domain.erros import (
    ArquivoExcedeLimite,
    DocumentoInacessivel,
    ErroDeDominio,
    ExtracaoNaoEncontrada,
    ServicoDeOcrIndisponivel,
    TipoDeArquivoNaoSuportado,
)
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.extracao import (
    IdentificadorDaExtracao,
    ResultadoDaExtracao,
    SituacaoDaExtracao,
)
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.interfaces.api.aplicacao import criar_aplicacao
from ocr_reader.interfaces.api.dependencias import (
    obter_caso_de_uso_de_consulta,
    obter_caso_de_uso_de_solicitacao,
    obter_configuracao,
)

_URI_VALIDO = "https://conta.blob.core.windows.net/container/arquivo.pdf?sig=abc"
_CONFIGURACAO_DE_TESTE = Configuracao(hosts_permitidos=["*.blob.core.windows.net"])


class _CasoDeUsoDeSolicitacaoFalso:
    """Dublê do caso de uso de solicitação: devolve uma extração ou levanta uma exceção fixa."""

    def __init__(
        self,
        extracao_solicitada: ExtracaoSolicitada | None = None,
        excecao: ErroDeDominio | None = None,
    ) -> None:
        self._extracao_solicitada = extracao_solicitada
        self._excecao = excecao
        self.chamadas = 0

    async def executar(self, endereco: EnderecoDeBlob) -> ExtracaoSolicitada:
        self.chamadas += 1
        if self._excecao is not None:
            raise self._excecao
        assert self._extracao_solicitada is not None
        return self._extracao_solicitada


class _CasoDeUsoDeConsultaFalso:
    """Dublê do caso de uso de consulta: devolve um resultado fixo ou levanta uma exceção fixa."""

    def __init__(
        self,
        resultado: ResultadoDaExtracao | None = None,
        excecao: ErroDeDominio | None = None,
    ) -> None:
        self._resultado = resultado
        self._excecao = excecao

    async def executar(self, identificador: IdentificadorDaExtracao) -> ResultadoDaExtracao:
        if self._excecao is not None:
            raise self._excecao
        assert self._resultado is not None
        return self._resultado


def _criar_cliente(
    caso_de_uso_de_solicitacao: _CasoDeUsoDeSolicitacaoFalso | None = None,
    caso_de_uso_de_consulta: _CasoDeUsoDeConsultaFalso | None = None,
) -> TestClient:
    app = criar_aplicacao()
    app.dependency_overrides[obter_configuracao] = lambda: _CONFIGURACAO_DE_TESTE
    if caso_de_uso_de_solicitacao is not None:
        app.dependency_overrides[obter_caso_de_uso_de_solicitacao] = (
            lambda: caso_de_uso_de_solicitacao
        )
    if caso_de_uso_de_consulta is not None:
        app.dependency_overrides[obter_caso_de_uso_de_consulta] = lambda: caso_de_uso_de_consulta
    return TestClient(app)


def test_post_extracoes_com_uri_valido_retorna_202_com_id_e_location() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        extracao_solicitada=ExtracaoSolicitada(
            identificador=IdentificadorDaExtracao(valor="op-123"),
            tipo_de_arquivo=TipoDeArquivo.PDF,
            tamanho_em_bytes=54321,
        )
    )

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 202
    assert resposta.json() == {"idExtracao": "op-123", "situacao": "processando"}
    assert resposta.headers["location"] == "/extracoes/op-123"
    assert caso_de_uso_falso.chamadas == 1


def test_post_extracoes_com_host_fora_da_allowlist_retorna_400_sem_chamar_o_caso_de_uso() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso()

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post(
            "/extracoes", json={"sasUri": "https://malicioso.com/arquivo.pdf?sig=abc"}
        )

    assert resposta.status_code == 400
    assert caso_de_uso_falso.chamadas == 0


def test_post_extracoes_com_tipo_nao_suportado_retorna_415() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        excecao=TipoDeArquivoNaoSuportado("tipo não aceito")
    )

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 415


def test_post_extracoes_com_arquivo_acima_do_limite_retorna_413() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        excecao=ArquivoExcedeLimite("arquivo grande demais")
    )

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 413


def test_post_extracoes_com_documento_inacessivel_retorna_502_sem_vazar_uri() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        excecao=DocumentoInacessivel("documento inacessível")
    )

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 502
    assert "sig=abc" not in resposta.text


def test_post_extracoes_com_falha_no_servico_de_ocr_retorna_502() -> None:
    caso_de_uso_falso = _CasoDeUsoDeSolicitacaoFalso(
        excecao=ServicoDeOcrIndisponivel("serviço de OCR indisponível")
    )

    with _criar_cliente(caso_de_uso_de_solicitacao=caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 502


def test_get_extracao_processando_retorna_202() -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        resultado=ResultadoDaExtracao(situacao=SituacaoDaExtracao.PROCESSANDO)
    )

    with _criar_cliente(caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/op-123")

    assert resposta.status_code == 202
    assert resposta.json() == {"situacao": "processando", "texto": None}


def test_get_extracao_concluida_retorna_200_com_texto() -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        resultado=ResultadoDaExtracao(situacao=SituacaoDaExtracao.CONCLUIDA, texto="ola mundo")
    )

    with _criar_cliente(caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/op-123")

    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "concluida", "texto": "ola mundo"}


def test_get_extracao_com_id_inexistente_retorna_404() -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        excecao=ExtracaoNaoEncontrada("não existe extração com esse id")
    )

    with _criar_cliente(caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/nao-existe")

    assert resposta.status_code == 404


def test_get_extracao_com_falha_no_servico_de_ocr_retorna_502() -> None:
    caso_de_uso_falso = _CasoDeUsoDeConsultaFalso(
        excecao=ServicoDeOcrIndisponivel("serviço de OCR indisponível")
    )

    with _criar_cliente(caso_de_uso_de_consulta=caso_de_uso_falso) as cliente:
        resposta = cliente.get("/extracoes/op-123")

    assert resposta.status_code == 502
