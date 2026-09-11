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

Todos os parâmetros usam prefixo `OCR_READER_` e podem ser configurados de duas formas:

### Método 1: Arquivo `.env` (recomendado)

1. Copie o modelo:
   ```bash
   cp .env.example .env
   ```

2. Edite `.env` com seus valores:
   ```env
   OCR_READER_HOSTS_PERMITIDOS=["*.blob.core.windows.net"]
   OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE=https://seu-recurso.cognitiveservices.azure.com
   OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE=sua-chave-de-acesso-aqui
   ```

3. Suba a API:
   ```bash
   uv run uvicorn ocr_reader.interfaces.api.aplicacao:app
   ```

⚠️ **Importante:** Nunca comite o arquivo `.env` (está no `.gitignore`). Ele permanece apenas na sua máquina.

### Método 2: Variáveis de Ambiente (`export`)

Alternativamente, use `export` para cada variável:

```bash
export OCR_READER_HOSTS_PERMITIDOS='["*.blob.core.windows.net"]'
export OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE="https://seu-recurso.cognitiveservices.azure.com"
export OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE="sua-chave-de-acesso-aqui"
uv run uvicorn ocr_reader.interfaces.api.aplicacao:app
```

### Precedência de Configuração

Variáveis de ambiente **sobrescrevem** valores do `.env`. Assim:

- **Em desenvolvimento:** Use `.env` para manter valores padrão
- **Em container/CI:** Configure pelo ambiente — garante que o segredo não seja versionado acidentalmente

### Variáveis Disponíveis

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OCR_READER_HOSTS_PERMITIDOS` | `["*.blob.core.windows.net"]` | JSON array de padrões de host aceitos (barreira SSRF) |
| `OCR_READER_TAMANHO_MAXIMO_EM_BYTES` | 524.288.000 (500 MB) | Tamanho máximo de arquivo aceito |
| `OCR_READER_JANELA_DE_CABECALHO_EM_BYTES` | 8.192 (8 KiB) | Janela inicial de leitura para detecção de tipo |
| `OCR_READER_JANELA_AMPLIADA_EM_BYTES` | 524.288 (512 KiB) | Janela estendida para redetecção (caso OOXML ambíguo) |
| `OCR_READER_TIMEOUT_EM_SEGUNDOS` | 10.0 | Timeout de requisições HTTP |
| `OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE` | (vazio) | **Obrigatório para OCR.** Endpoint do Azure Document Intelligence |
| `OCR_READER_CHAVE_DO_DOCUMENT_INTELLIGENCE` | (vazio) | **Obrigatório para OCR. Segredo.** Chave de acesso do Azure Document Intelligence |
| `OCR_READER_ID_DO_MODELO_DE_OCR` | `prebuilt-read` | Modelo de OCR no Azure |
| `OCR_READER_VERSAO_DA_API_DE_OCR` | `2024-11-30` | Versão da API do Document Intelligence |

**Nota sobre `HOSTS_PERMITIDOS`:** No `.env`, use JSON array: `["*.blob.core.windows.net"]` ou `["*.blob.core.windows.net", "meu-dominio.blob.core.windows.net"]`. Com `export`, a sintaxe é a mesma.

## Observabilidade

A API emite eventos em **log estruturado** (JSON no stdout) para você calcular métricas de operação. Cada linha é um objeto JSON parseável, pronto para ingestão por ferramentas de agregação (Application Insights, Datadog, Loki, etc.) sem precisar de parser customizado.

### Eventos Emitidos

#### 1. `extracao_solicitada` — Quando um POST aceita o documento

Emitido imediatamente após validação bem-sucedida e submissão ao Azure.

Exemplo:
```json
{"timestamp": "2026-09-11 14:09:39,080", "nivel": "INFO", "mensagem": "extracao_solicitada", "evento": "extracao_solicitada", "id_extracao": "abc-123", "tipo_de_arquivo": "pdf", "tamanho_em_bytes": 15970686}
```

**Campos:**
- `evento`: `"extracao_solicitada"`
- `id_extracao`: Identificador único para correlacionar com o `GET` de consulta
- `tipo_de_arquivo`: Um de: `pdf`, `docx`, `xlsx`, `pptx`, `html`, `jpeg`, `png`, `bmp`, `tiff`, `heif`
- `tamanho_em_bytes`: Tamanho total do blob lido do Azure

#### 2. `extracao_concluida` — Quando um GET retorna sucesso

Emitido apenas quando a extração terminou (`situacao=concluida`) e o Azure forneceu os dados de duração e número de páginas. Se esses dados faltarem, nenhum evento de conclusão é emitido — a requisição responde normalmente mesmo assim.

Exemplo:
```json
{"timestamp": "2026-09-11 14:09:42,330", "nivel": "INFO", "mensagem": "extracao_concluida", "evento": "extracao_concluida", "id_extracao": "abc-123", "duracao_do_ocr_em_ms": 3250, "quantidade_de_paginas": 12}
```

**Campos:**
- `evento`: `"extracao_concluida"`
- `id_extracao`: Mesmo identificador do POST, permite correlacionar requisições
- `duracao_do_ocr_em_ms`: Duração do processamento **no serviço Azure**, em milissegundos — **não é latência da nossa API**
- `quantidade_de_paginas`: Número de páginas analisadas

### Calculando Métricas

Com esses dois eventos, você pode calcular:

**Tempo por página:** 
```
3250 ms / 12 páginas = 270,8 ms/página
```

**Tempo por MB:**
```
15970686 bytes / 1048576 = 15,24 MB
3250 ms / 15,24 MB = 213,4 ms/MB
```

**Correlação de requisições:**
Use `id_extracao` para conectar o evento de solicitação (tamanho, tipo) com o de conclusão (duração, páginas).

### Sobre os Dados

- **Duração:** Vem do Azure (`createdDateTime` a `lastUpdatedDateTime` na resposta de `analyzeResults`). Mede o tempo de processamento do serviço, não a latência da nossa API nem do cliente.
- **Número de páginas:** Contagem de páginas analisadas. Para imagens, é 1.
- **Métrica ausente:** Se o Azure não devolver esses dados, o evento de conclusão não é emitido. Isso não é erro — requisição responde normalmente com `200 OK`. Métricas ausentes nunca travam uma requisição.

### Segurança no Log

**Nenhum log contém:**
- SAS URI ou sua query de assinatura (`sig=...`)
- Chave do Document Intelligence

Os eventos emitem apenas IDs e métricas numéricas — seguros para agregar e indexar.

### Contrato HTTP Não Mudou

Os corpos de resposta continuam idênticos. Log estruturado é **observabilidade**, não **API pública**. Os eventos são um detalhe de implementação que podem evoluir sem quebrar clientes.

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
