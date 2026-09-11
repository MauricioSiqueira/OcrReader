# OCR Reader — API de Validação de Documentos Remotos

Uma API FastAPI que valida documentos remotos armazenados em Azure Blob Storage, detectando o tipo de arquivo lendo apenas os primeiros bytes (via HTTP Range), antes de delegar o OCR ao Azure Document Intelligence.

## Funcionalidade

A API recebe um SAS URI de blob, valida:

- **Esquema e segurança:** URI deve ser `https` com host na allowlist (padrão: `*.blob.core.windows.net`)
- **Assinatura:** Presença de query de assinatura (SAS)
- **Tamanho:** Arquivo não excede o limite configurado (padrão: 500 MB)
- **Tipo:** Magic bytes revelam um tipo de arquivo aceito

Se aprovado, responde com `200` e o tipo detectado. A API **não baixa o arquivo inteiro** — lê apenas ~8 KB via Range request para extrair magic bytes.

Tipos aceitos: PDF, DOCX, XLSX, PPTX, HTML, JPEG, PNG, BMP, TIFF, HEIF.

## Instalação

### Pré-requisitos

- **Python 3.12+**
- **libmagic** (biblioteca nativa, necessária para detecção de tipo)

### Passos

1. **Instalar libmagic:**

   ```bash
   brew install libmagic
   ```

2. **Instalar dependências do projeto com `uv`:**

   ```bash
   uv sync
   ```

   Isso instala o código da API e todas as dependências (FastAPI, httpx, python-magic, etc.) em um ambiente virtual.

## Execução

### Iniciar o servidor

```bash
uv run uvicorn ocr_reader.interfaces.api.aplicacao:app --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`.

Para recarregar automaticamente durante desenvolvimento:

```bash
uv run uvicorn ocr_reader.interfaces.api.aplicacao:app --reload
```

### Testar a API

**POST /extracoes** — Valida um documento remoto

Corpo da requisição (JSON):

```json
{
  "sasUri": "https://conta.blob.core.windows.net/container/documento.pdf?sv=2024-XX-XX&..."
}
```

Resposta de sucesso (200 OK):

```json
{
  "tipoDeArquivo": "pdf"
}
```

Respostas de erro:

- `400 Bad Request`: URI inválido (schema, host não permitido, sem assinatura SAS)
- `413 Payload Too Large`: Arquivo excede o limite de tamanho
- `415 Unsupported Media Type`: Tipo de arquivo não aceito
- `502 Bad Gateway`: Blob inacessível (rede, autorização, SAS expirado)

## Testes Automatizados

Executar a suíte de testes:

```bash
uv run pytest
```

Os testes cobrem:
- Validação de endereço (URI, host, assinatura)
- Detecção de tipo de arquivo (magic bytes, caso OOXML)
- Tamanho de arquivo
- Cenários de erro (acesso negado, SAS expirado, etc.)

## Configuração

### Variáveis de Ambiente

Todos os parâmetros podem ser configurados via variáveis com prefixo `OCR_READER_`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OCR_READER_HOSTS_PERMITIDOS` | `*.blob.core.windows.net` | Lista de padrões de host aceitos (separados por vírgula) |
| `OCR_READER_TAMANHO_MAXIMO_EM_BYTES` | 524.288.000 (500 MB) | Tamanho máximo de arquivo aceito |
| `OCR_READER_JANELA_DE_CABECALHO_EM_BYTES` | 8.192 (8 KiB) | Janela inicial de leitura para detecção de tipo |
| `OCR_READER_JANELA_AMPLIADA_EM_BYTES` | 524.288 (512 KiB) | Janela estendida para redetecção (caso OOXML ambíguo) |
| `OCR_READER_TIMEOUT_EM_SEGUNDOS` | 10.0 | Timeout de requisições HTTP |

Exemplo de uso:

```bash
export OCR_READER_HOSTS_PERMITIDOS="*.blob.core.windows.net,meu-dominio.blob.core.windows.net"
export OCR_READER_TAMANHO_MAXIMO_EM_BYTES=104857600  # 100 MB
uv run uvicorn ocr_reader.interfaces.api.aplicacao:app
```

## Segurança

- **Sem vazamento de SAS URI:** O URI de assinatura nunca aparece em logs, respostas de erro ou tracebacks. A validação de endereço acontece **antes** de qualquer requisição de rede.
- **Barreira SSRF:** A allowlist de hosts (padrão: `*.blob.core.windows.net`) previne requisições a hosts arbitrários.
- **Detecção de tipo apenas:** A API valida apenas o cabeçalho (~8 KB). Um arquivo com cabeçalho válido mas corpo corrompido passa pela validação e falha no OCR — isso é trade-off entre segurança e eficiência de rede.

## Estrutura do Código

```
src/ocr_reader/
  domain/              Entidades, value objects, regras de negócio
  application/         Casos de uso, orquestração
  infrastructure/      Adaptadores (HTTP, magic bytes, configuração)
  interfaces/          Camada HTTP (rotas, DTOs, injeção de dependência)

tests/                 Testes espelhando a estrutura de src/
```

A arquitetura segue princípios de **Clean Architecture**: o domínio não conhece frameworks; dependências concretas entram por injeção contra abstrações (Protocols).

## Licença

Propriedade de [Organização]. Não disponível publicamente.
