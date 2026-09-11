"""Testes de integração HTTP da rota `POST /extracoes`.

O caso de uso é substituído por um dublê: a orquestração de leitura/detecção já é coberta pelos
testes de `application` e `infrastructure`. Aqui o que se verifica é o comportamento da camada
HTTP — parsing do DTO, tradução de erro de domínio para status HTTP e a garantia de que um
endereço inválido nunca chega a acionar o caso de uso (logo, nunca gera requisição de rede).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from ocr_reader.application.casos_de_uso.validar_documento_remoto import VeredictoDeValidacao
from ocr_reader.domain.erros import (
    ArquivoExcedeLimite,
    DocumentoInacessivel,
    ErroDeDominio,
    TipoDeArquivoNaoSuportado,
)
from ocr_reader.domain.modelos.endereco_de_blob import EnderecoDeBlob
from ocr_reader.domain.modelos.tipo_de_arquivo import TipoDeArquivo
from ocr_reader.infrastructure.configuracao import Configuracao
from ocr_reader.interfaces.api.aplicacao import criar_aplicacao
from ocr_reader.interfaces.api.dependencias import (
    obter_caso_de_uso_de_validacao,
    obter_configuracao,
)

_URI_VALIDO = "https://conta.blob.core.windows.net/container/arquivo.pdf?sig=abc"
_CONFIGURACAO_DE_TESTE = Configuracao(hosts_permitidos=["*.blob.core.windows.net"])


class _CasoDeUsoDeValidacaoFalso:
    """Dublê do caso de uso: devolve um veredicto fixo ou levanta uma exceção fixa."""

    def __init__(
        self,
        veredicto: VeredictoDeValidacao | None = None,
        excecao: ErroDeDominio | None = None,
    ) -> None:
        self._veredicto = veredicto
        self._excecao = excecao
        self.chamadas = 0

    async def executar(self, endereco: EnderecoDeBlob) -> VeredictoDeValidacao:
        self.chamadas += 1
        if self._excecao is not None:
            raise self._excecao
        assert self._veredicto is not None
        return self._veredicto


def _criar_cliente(caso_de_uso_falso: _CasoDeUsoDeValidacaoFalso) -> TestClient:
    app = criar_aplicacao()
    app.dependency_overrides[obter_configuracao] = lambda: _CONFIGURACAO_DE_TESTE
    app.dependency_overrides[obter_caso_de_uso_de_validacao] = lambda: caso_de_uso_falso
    return TestClient(app)


def test_post_extracoes_com_uri_valido_retorna_200_com_tipo_detectado() -> None:
    caso_de_uso_falso = _CasoDeUsoDeValidacaoFalso(
        veredicto=VeredictoDeValidacao(tipo_de_arquivo=TipoDeArquivo.PDF)
    )

    with _criar_cliente(caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 200
    assert resposta.json() == {"tipoDeArquivo": "pdf"}
    assert caso_de_uso_falso.chamadas == 1


def test_post_extracoes_com_host_fora_da_allowlist_retorna_400_sem_chamar_caso_de_uso() -> None:
    caso_de_uso_falso = _CasoDeUsoDeValidacaoFalso()

    with _criar_cliente(caso_de_uso_falso) as cliente:
        resposta = cliente.post(
            "/extracoes", json={"sasUri": "https://malicioso.com/arquivo.pdf?sig=abc"}
        )

    assert resposta.status_code == 400
    assert caso_de_uso_falso.chamadas == 0


def test_post_extracoes_com_tipo_nao_suportado_retorna_415() -> None:
    caso_de_uso_falso = _CasoDeUsoDeValidacaoFalso(
        excecao=TipoDeArquivoNaoSuportado("tipo não aceito")
    )

    with _criar_cliente(caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 415


def test_post_extracoes_com_arquivo_acima_do_limite_retorna_413() -> None:
    caso_de_uso_falso = _CasoDeUsoDeValidacaoFalso(
        excecao=ArquivoExcedeLimite("arquivo grande demais")
    )

    with _criar_cliente(caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 413


def test_post_extracoes_com_documento_inacessivel_retorna_502_sem_vazar_uri() -> None:
    caso_de_uso_falso = _CasoDeUsoDeValidacaoFalso(
        excecao=DocumentoInacessivel("documento inacessível")
    )

    with _criar_cliente(caso_de_uso_falso) as cliente:
        resposta = cliente.post("/extracoes", json={"sasUri": _URI_VALIDO})

    assert resposta.status_code == 502
    assert "sig=abc" not in resposta.text
