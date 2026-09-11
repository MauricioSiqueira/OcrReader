# OCR Reader — API de Extração de Texto com OCR

Uma API FastAPI que extrai texto de documentos remotos armazenados em Azure Blob Storage. Valida cada documento lendo apenas os primeiros bytes (via HTTP Range), depois delega o OCR ao Azure Document Intelligence.

## Funcionalidade

A API recebe um SAS URI de blob e executa uma pipeline de duas etapas:

1. **Validação (antes de qualquer OCR):**
   - Esquema e segurança: URI deve ser `https` com host na allowlist (padrão: `*.blob.core.windows.net`)
   - Assinatura: Presença de query de assinatura (SAS)
   - Tamanho: Arquivo não excede o limite configurado (padrão: 500 MB)
   - Tipo: Magic bytes revelam um tipo de arquivo aceito

2. **Extração de texto:** Se validado, o documento é enviado ao Azure Document Intelligence (`prebuilt-read`) e o texto extraído fica disponível para consulta.

A API **não baixa o arquivo inteiro** — lê apenas ~8 KB via Range request para validação, depois passa o SAS URI ao Azure para o OCR em si. Assim, o arquivo transita diretamente entre o blob e o serviço de OCR, sem cópia intermediária na nossa máquina.

Tipos aceitos: PDF, DOCX, XLSX, PPTX, HTML, JPEG, PNG, BMP, TIFF, HEIF.

**Arquitetura:** A API é **sem estado**. O identificador devolvido ao cliente é o `operation_id` do Azure. Não há banco, cache nem fila — cada instância da API consulta o Azure independentemente.

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

#### 1. POST /extracoes — Solicitar extração de texto

Corpo da requisição (JSON):

```json
{
  "sasUri": "https://conta.blob.core.windows.net/container/documento.pdf?sv=2024-XX-XX&sig=..."
}
```

Resposta de aceite (202 Accepted):

```json
{
  "idExtracao": "a1b2c3d4-e5f6-...",
  "situacao": "processando"
}
```

Header de resposta `Location: /extracoes/a1b2c3d4-e5f6-...` aponta para onde consultar o resultado.

**Rejeições (antes de qualquer OCR):**

- `400 Bad Request`: URI inválido (schema, host não permitido, sem assinatura SAS)
- `413 Payload Too Large`: Arquivo excede o limite de tamanho
- `415 Unsupported Media Type`: Tipo de arquivo não aceito
- `502 Bad Gateway`: Blob inacessível (rede, autorização, SAS expirado)

#### 2. GET /extracoes/{idExtracao} — Consultar resultado da extração

Resposta enquanto processa (202 Accepted):

```json
{
  "situacao": "processando",
  "texto": null
}
```

Resposta quando concluída (200 OK):

```json
{
  "situacao": "concluida",
  "texto": "Lorem ipsum dolor sit amet, consectetur adipiscing elit..."
}
```

**Respostas de erro:**

- `202 Accepted`: Extração ainda em processamento
- `404 Not Found`: ID de extração não existe
- `502 Bad Gateway`: Falha no serviço de OCR

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
| `OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE` | (vazio) | **Obrigatório em produção.** Endpoint do Azure Document Intelligence (ex.: `https://seu-recurso.cognitiveservices.azure.com`) |
| `OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE` | (vazio) | **Obrigatório em produção. Credencial.** Chave de acesso (subscription key) do Azure Document Intelligence. **Nunca comitar.** |
| `OCR_READER_ID_DO_MODELO_DE_OCR` | `prebuilt-read` | ID do modelo de OCR no Azure (não altere a menos que Azure offereça outro) |
| `OCR_READER_VERSAO_DA_API_DE_OCR` | `2024-11-30` | Versão da API do Document Intelligence (compatível com o endpoint) |

#### Exemplo: Configuração para produção com Azure Document Intelligence

```bash
# Validação de blob
export OCR_READER_HOSTS_PERMITIDOS="*.blob.core.windows.net"
export OCR_READER_TAMANHO_MAXIMO_EM_BYTES=524288000

# Azure Document Intelligence — obrigatórios para OCR funcionar
export OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE="https://seu-recurso.cognitiveservices.azure.com"
export OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE="sua-chave-de-acesso-aqui"

# Rodar a API
uv run uvicorn ocr_reader.interfaces.api.aplicacao:app --host 0.0.0.0 --port 8000
```

⚠️ **Segurança:** A chave do Document Intelligence é um segredo. **Nunca a comite no repositório.** Use um arquivo `.env` local (adicionado a `.gitignore`) ou um serviço de secrets em produção.

## Segurança

- **Sem vazamento de SAS URI:** O URI de assinatura nunca aparece em logs, respostas de erro ou tracebacks. A validação de endereço acontece **antes** de qualquer requisição de rede.
- **Chave do Document Intelligence protegida:** A chave é armazenada como `SecretStr` e nunca é exibida em `repr` ou mensagens de erro. Se a submissão ou consulta ao Azure falhar, a resposta é genérica: "Não foi possível..." — nunca vaza credencial.
- **Sem estado local:** Não há banco, cache nem dicionário em memória armazenando operações. O único "estado" é o que o Azure mantém. Assim, cada requisição `GET /extracoes/{id}` é uma nova consulta ao serviço — mais seguro contra ataques de timing ou enumeração.
- **Barreira SSRF:** A allowlist de hosts (padrão: `*.blob.core.windows.net`) previne requisições a hosts arbitrários.
- **Validação antes de OCR:** A API valida arquivo e endereço antes de enviar ao Azure. Um arquivo com cabeçalho válido mas corpo corrompido passa pela validação e falha no OCR — isso é trade-off entre segurança e eficiência de rede.

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
