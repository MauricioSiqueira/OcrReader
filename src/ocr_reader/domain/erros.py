"""Exceções de domínio da validação de documento remoto e da extração de texto via OCR."""

from __future__ import annotations


class ErroDeDominio(Exception):
    """Classe base das exceções previstas pelas regras de negócio desta API."""


class EnderecoInvalido(ErroDeDominio):
    """O endereço informado não atende aos requisitos de um endereço de blob aceito."""


class TipoDeArquivoNaoSuportado(ErroDeDominio):
    """O arquivo detectado não está entre os tipos aceitos para extração."""


class ArquivoExcedeLimite(ErroDeDominio):
    """O tamanho total do arquivo excede o limite configurado."""


class DocumentoInacessivel(ErroDeDominio):
    """O blob remoto não pôde ser lido: rede, autorização ou SAS expirado."""


class ExtracaoNaoEncontrada(ErroDeDominio):
    """Não existe extração com o identificador informado."""


class ServicoDeOcrIndisponivel(ErroDeDominio):
    """O serviço de OCR não pôde ser acionado, falhou ao processar ou não pôde ser consultado."""
