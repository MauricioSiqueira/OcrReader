"""Value object que representa um endereço de blob validado para leitura remota."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from ocr_reader.domain.erros import EnderecoInvalido

_ESQUEMA_EXIGIDO = "https"
_CORINGA_DE_SUBDOMINIO = "*."


@dataclass(frozen=True, slots=True, repr=False)
class EnderecoDeBlob:
    """Endereço de blob (SAS URI) já validado contra as regras de segurança da API.

    Só é possível obter uma instância através de `criar`, que aplica as validações. O `repr`
    oculta a query de assinatura para que o endereço nunca vaze em log ou traceback.
    """

    uri: str

    @staticmethod
    def criar(uri: str, hosts_permitidos: Collection[str]) -> EnderecoDeBlob:
        """Valida e constrói um `EnderecoDeBlob`.

        Args:
            uri: URI completo informado pelo consumidor, incluindo a query de assinatura.
            hosts_permitidos: Padrões de host aceitos (ex.: `"*.blob.core.windows.net"`).

        Returns:
            Instância validada de `EnderecoDeBlob`.

        Raises:
            EnderecoInvalido: se o esquema não é `https`, o host não está na allowlist ou a
                query de assinatura está ausente.
        """
        partes = urlsplit(uri)

        if partes.scheme != _ESQUEMA_EXIGIDO:
            raise EnderecoInvalido("Endereço de blob deve usar o esquema https.")

        if not partes.hostname or not _host_permitido(partes.hostname, hosts_permitidos):
            raise EnderecoInvalido("Host do endereço de blob não está na allowlist.")

        if not partes.query:
            raise EnderecoInvalido("Endereço de blob não traz query de assinatura (SAS).")

        return EnderecoDeBlob(uri=uri)

    def __repr__(self) -> str:
        partes = urlsplit(self.uri)
        uri_sem_assinatura = urlunsplit((partes.scheme, partes.netloc, partes.path, "", ""))
        return f"EnderecoDeBlob(uri={uri_sem_assinatura!r})"


def _host_permitido(host: str, hosts_permitidos: Collection[str]) -> bool:
    """Verifica se `host` casa com algum padrão da allowlist (`*.sufixo` ou host exato)."""
    host = host.lower()
    for padrao in hosts_permitidos:
        padrao = padrao.lower()
        if padrao.startswith(_CORINGA_DE_SUBDOMINIO):
            sufixo = padrao[1:]  # remove só o "*", mantém o ponto separador
            if host.endswith(sufixo) and host != sufixo[1:]:
                return True
        elif host == padrao:
            return True
    return False
