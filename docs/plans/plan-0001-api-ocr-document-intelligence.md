# plan-0001 — API de OCR sobre Azure Document Intelligence

**Estado:** aprovado pelo usuário em 2026-09-11
**Tarefa em curso:** `docs/tasks/feat-0001-fundacao-e-validacao-de-documento-remoto.md`
**Tarefa seguinte:** `feat-0002`, a ser escrita quando a `feat-0001` for integrada

## Contexto

O repositório tem hoje apenas as convenções de processo: nenhuma linha de Python, `docs/plans/` e
`docs/tasks/` vazios. Esta é a primeira entrega de código do projeto.

Sistemas internos guardam documentos em blobs da Azure e precisam do texto deles. Sem esta API, cada
consumidor falaria direto com o Document Intelligence, repetindo validação e espalhando credencial.
Esta API centraliza isso atrás de um contrato único.

O escopo é deliberadamente estreito, por decisão do usuário: **receber um SAS URI, validar que o
arquivo é de um tipo permitido, e delegar o OCR ao Azure Document Intelligence.** Nenhum outro motor
de OCR — Tesseract, PaddleOCR e EasyOCR estão explicitamente fora, agora e depois.

## Decisões tomadas com o usuário

| Decisão | Escolha | Alternativa descartada e porquê |
|---|---|---|
| Interface | API HTTP com FastAPI | CLI e biblioteca: o consumidor é outro serviço, não uma pessoa |
| Resposta | Assíncrona: `202` com id, consulta por `GET` | Síncrona: OCR de PDF grande estoura timeout de gateway |
| Modelo do DI | `prebuilt-read` | `prebuilt-layout` custa vários múltiplos por página e só compensa se as tabelas precisarem chegar estruturadas |
| Download | Só o cabeçalho; SAS URI repassado ao Azure | Baixar inteiro: o arquivo atravessaria nossa máquina duas vezes |
| Toolchain | `uv` + Python 3.12 | Python 3.9.6 do sistema já saiu do suporte de segurança; Poetry é mais lento |

## Fatos verificados na documentação

Conferidos em `learn.microsoft.com` antes de fixar o desenho, não de memória:

- API v4.0 GA, versão `2024-11-30`.
- `prebuilt-read` aceita PDF, JPEG/JPG, PNG, BMP, TIFF, HEIF, DOCX, XLSX, PPTX e HTML.
- Limite de arquivo: 500 MB no tier pago (S0), 4 MB no gratuito (F0). PDFs e TIFFs até 2.000 páginas.
- Imagens entre 50x50 e 10.000x10.000 pixels. PDF protegido por senha é rejeitado pelo serviço.
- Pacote Python: `azure-ai-documentintelligence`.
- Submissão por URL: `client.begin_analyze_document("prebuilt-read", AnalyzeDocumentRequest(url_source=uri))`.
- O id da operação sai em `poller.details["operation_id"]`.
- Contrato REST de consulta: `GET /documentModels/{modelId}/analyzeResults/{resultId}`.

## A ideia central

O Document Intelligence busca o blob sozinho quando recebe a URL. Isso permite que o arquivo **nunca
atravesse nossa API**: lemos cerca de 8 KB via `Range` só para conferir os magic bytes e, aprovado,
passamos o SAS URI adiante. O consumo de RAM fica constante, independente do tamanho do arquivo, e o
tráfego pesado acontece dentro da Azure.

Como consequência, a API fica **sem estado**: nosso id de extração é o `operation_id` do Azure e o
`GET` consulta o serviço. Não há banco, cache nem fila para manter — escala horizontalmente sem
coordenação entre instâncias.

Ressalva registrada: validamos o início do arquivo, não o conteúdo inteiro. Um arquivo com cabeçalho
de PDF e corpo corrompido passa por nós e falha no Azure. O erro chega ao cliente na consulta, não na
submissão. O custo de fechar essa brecha seria baixar tudo — exatamente o que a decisão acima recusa.

## Arquitetura

Regra de dependência conforme `CLAUDE.md`: as setas apontam para dentro.

```
src/ocr_reader/
  domain/
    modelos/tipo_de_arquivo.py          # enum TipoDeArquivo + catálogo de tipos aceitos
    modelos/endereco_de_blob.py         # VO: SAS URI validado
    modelos/extracao.py                 # IdentificadorDaExtracao, SituacaoDaExtracao, ResultadoDaExtracao
    portas/leitor_de_bytes_remotos.py   # Protocol
    portas/detector_de_tipo_de_arquivo.py
    portas/servico_de_ocr.py
    erros.py
  application/
    casos_de_uso/solicitar_extracao_de_texto.py
    casos_de_uso/consultar_extracao_de_texto.py
  infrastructure/
    http/leitor_de_bytes_httpx.py
    deteccao/detector_libmagic.py
    azure/servico_de_ocr_document_intelligence.py
    configuracao.py
  interfaces/
    api/aplicacao.py
    api/rotas/extracoes.py
    api/esquemas.py
    api/dependencias.py
    api/tratadores_de_erro.py
```

O domínio não conhece `httpx`, `magic`, `azure` nem `fastapi`. Os três Protocols são a fronteira, e
toda dependência concreta entra por injeção.

**Nomenclatura em português** no domínio e nos casos de uso, seguindo o padrão dos outros projetos do
usuário. Bibliotecas externas mantêm seus nomes originais.

## Fluxo

### `POST /extracoes`

Corpo: `{"sasUri": "https://conta.blob.core.windows.net/..."}`

1. Valida o URI: esquema `https`, host na allowlist (padrão `*.blob.core.windows.net`), query de SAS
   presente. É a barreira contra SSRF — sem ela a API vira um buscador de URLs arbitrárias para quem
   quiser alcançar a rede interna.
2. `GET` com `Range: bytes=0-8191`. O tamanho total sai do `Content-Range`.
3. Tamanho acima do limite configurado devolve `413`.
4. `libmagic` sobre o cabeçalho devolve o tipo.
5. **Armadilha do OOXML**: DOCX e XLSX são arquivos ZIP. Se a detecção voltar ZIP genérico, faz uma
   segunda leitura mais larga (512 KiB) e redetecta; persistindo genérico, devolve `415`.
6. Tipo fora da lista aceita devolve `415`.
7. `begin_analyze_document("prebuilt-read", AnalyzeDocumentRequest(url_source=uri))`.
8. `202` com `{"idExtracao": "...", "situacao": "processando"}` e header `Location: /extracoes/{id}`.

### `GET /extracoes/{id}`

`200` com o texto extraído, `202` enquanto processa, `404` se o id não existe, `502` se o Azure
devolveu falha.

## Ponto a resolver na implementação

O SDK documenta `get_analyze_result_pdf` e `get_analyze_result_figure`, mas não um método público
para buscar o JSON por `result_id`. Duas saídas, nesta ordem de preferência:

1. `poller.continuation_token()` na submissão e retomada por `continuation_token=` na consulta — o
   caminho canônico dos SDKs Azure para operações longas.
2. `GET` direto no REST com `httpx`, no contrato documentado acima, com header
   `Ocp-Apim-Subscription-Key`.

O `Naja` verifica qual funciona na versão instalada e reporta. A porta `ServicoDeOcr` isola a
escolha: nenhuma outra camada muda em função dela.

## Riscos registrados

- **`libmagic` é biblioteca nativa.** Precisa de `brew install libmagic` na máquina e de `libmagic1`
  na imagem de container. A alternativa pura em Python (`filetype`) é mais fraca justamente em OOXML,
  que é o caso difícil aqui.
- **Validade do SAS.** O Azure baixa o blob depois da nossa resposta. SAS de validade curta pode
  expirar antes de o serviço chegar nele.
- **O SAS URI é credencial.** Não pode aparecer em log, mensagem de erro ou traceback. Item
  obrigatório de revisão.
- **Alcance de rede.** Se a conta de armazenamento restringe acesso por VNet ou firewall, o Azure não
  busca o blob e o `url_source` falha. Só aparece em ambiente real.
- **Tier gratuito (F0)** corta em 4 MB e processa só as duas primeiras páginas; o comportamento
  diverge da produção em teste manual.

## Fora de escopo

Autenticação da nossa API, rate limiting, persistência de resultados, webhook de conclusão,
observabilidade além de log estruturado, Docker e pipeline de CI. Qualquer motor de OCR local.

## Divisão em tarefas

**`feat-0001` — Fundação e validação de documento remoto.** Toolchain, estrutura de camadas, domínio,
portas, adaptadores `httpx` e `libmagic`, caso de uso de validação e `POST /extracoes` respondendo
`200` com o tipo detectado. Sem OCR.

**`feat-0002` — OCR via Azure Document Intelligence.** Porta `ServicoDeOcr`, adaptador do SDK,
configuração de credencial, `POST` passando a devolver `202` e nascimento do `GET /extracoes/{id}`.

Motivo do corte: a validação é testável sem credencial nem rede; o adaptador Azure não é. Numa tarefa
só, metade dos testes dependeria de segredo.
