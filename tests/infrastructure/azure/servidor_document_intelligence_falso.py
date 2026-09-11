"""Servidor HTTP local real que simula o Document Intelligence, para testar o adaptador sem rede.

Usa `aiohttp` (a mesma biblioteca do transporte assíncrono do SDK) para que o adaptador fale HTTP
de verdade com um servidor em `127.0.0.1`, em vez de precisar reimplementar a interface interna de
transporte do `azure-core` só para os testes.
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

ID_DO_MODELO = "prebuilt-read"
VERSAO_DA_API = "2024-11-30"
_PREFIXO_DA_API = "/documentintelligence"


class ServidorDocumentIntelligenceFalso:
    """Simula a submissão (`POST ...:analyze`) e a consulta (`GET .../analyzeResults/{id}`)."""

    def __init__(self) -> None:
        self.operation_id = "11111111-2222-3333-4444-555555555555"
        self.falhar_submissao = False
        self.corpo_da_consulta: dict[str, Any] = {"status": "running"}
        self.status_http_da_consulta = 200
        self.endpoint = ""
        self._runner: web.AppRunner | None = None

    async def iniciar(self) -> None:
        """Sobe o servidor em uma porta efêmera de `127.0.0.1` e preenche `self.endpoint`."""
        app = web.Application()
        app.router.add_post(
            f"{_PREFIXO_DA_API}/documentModels/{ID_DO_MODELO}:analyze", self._submeter
        )
        app.router.add_get(
            f"{_PREFIXO_DA_API}/documentModels/{ID_DO_MODELO}/analyzeResults/{{id_da_operacao}}",
            self._consultar,
        )
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await site.start()
        porta = self._runner.addresses[0][1]
        self.endpoint = f"http://127.0.0.1:{porta}"

    async def encerrar(self) -> None:
        """Libera o servidor e a porta."""
        if self._runner is not None:
            await self._runner.cleanup()

    async def _submeter(self, request: web.Request) -> web.Response:
        if self.falhar_submissao:
            return web.json_response({"error": {"message": "falha simulada"}}, status=500)

        localizacao_da_operacao = (
            f"{self.endpoint}{_PREFIXO_DA_API}/documentModels/{ID_DO_MODELO}/analyzeResults/"
            f"{self.operation_id}?api-version={VERSAO_DA_API}"
        )
        return web.json_response(
            {}, status=202, headers={"Operation-Location": localizacao_da_operacao}
        )

    async def _consultar(self, request: web.Request) -> web.Response:
        return web.json_response(self.corpo_da_consulta, status=self.status_http_da_consulta)
