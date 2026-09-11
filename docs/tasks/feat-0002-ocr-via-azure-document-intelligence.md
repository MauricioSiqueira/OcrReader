# feat-0002 — OCR via Azure Document Intelligence

**Plano de origem:** docs/plans/plan-0001-api-ocr-document-intelligence.md
**Branch:** feat/0002-ocr-via-azure-document-intelligence
**Depende de:** feat-0001 (mesclada na `main` pela PR #1)

## Objetivo

Depois de aprovado na validação, o documento é enviado ao Azure Document Intelligence e o texto
extraído fica disponível por consulta — a API passa a fazer OCR de fato.

## Escopo

- [ ] Dependência `azure-ai-documentintelligence` no `pyproject.toml`.
- [ ] `domain/modelos/extracao.py`: `IdentificadorDaExtracao` (value object),
      `SituacaoDaExtracao` (enum: `PROCESSANDO`, `CONCLUIDA`, `FALHOU`) e `ResultadoDaExtracao`
      (situação + texto quando concluída).
- [ ] `domain/portas/servico_de_ocr.py`: `Protocol` com `solicitar_leitura(endereco)` devolvendo
      `IdentificadorDaExtracao` e `obter_leitura(identificador)` devolvendo `ResultadoDaExtracao`.
- [ ] `domain/erros.py`: acrescentar `ExtracaoNaoEncontrada` e `ServicoDeOcrIndisponivel`.
- [ ] `infrastructure/azure/servico_de_ocr_document_intelligence.py`: adaptador com
      `DocumentIntelligenceClient` assíncrono, submetendo por URL com
      `begin_analyze_document("prebuilt-read", AnalyzeDocumentRequest(url_source=...))`.
- [ ] `infrastructure/configuracao.py`: acrescentar endpoint, chave (`SecretStr`), id do modelo
      (padrão `prebuilt-read`) e versão da API (padrão `2024-11-30`).
- [ ] `application/casos_de_uso/solicitar_extracao_de_texto.py`: reaproveita a validação da
      `feat-0001` e, aprovada, solicita a leitura. **Não duplique a lógica de validação** — componha
      com o caso de uso existente.
- [ ] `application/casos_de_uso/consultar_extracao_de_texto.py`.
- [ ] `POST /extracoes` passa a responder `202` com `{"idExtracao": ..., "situacao": "processando"}`
      e header `Location: /extracoes/{id}`. O `200` da `feat-0001` deixa de existir.
- [ ] `GET /extracoes/{id}`: `200` com o texto quando concluída, `202` enquanto processa,
      `404` se o id não existe, `502` se o serviço falhou.
- [ ] Testes cobrindo o adaptador com transporte HTTP mockado e as duas rotas com porta falsa.
      Atualizar os testes da `feat-0001` que esperavam `200` no `POST`.

## Fora de escopo

- Persistência de resultados, fila, webhook de conclusão, cache.
- Autenticação da nossa API, rate limiting, Docker, CI.
- `prebuilt-layout` ou qualquer outro modelo além de `prebuilt-read`.
- Qualquer motor de OCR local. Proibido, agora e sempre.

## Critérios de aceite

- `POST /extracoes` com SAS URI de PDF válido responde `202` com id e header `Location`.
- As rejeições da `feat-0001` continuam idênticas: `400` fora da allowlist, `415` tipo não aceito,
  `413` acima do limite — e **nenhuma delas chega a chamar o serviço de OCR**.
- `GET /extracoes/{id}` devolve `202` enquanto processa e `200` com o texto quando concluída.
- `GET` com id inexistente responde `404`.
- Falha do Document Intelligence vira `502`, sem vazar a chave nem o SAS URI.
- A chave da Azure não aparece em log, resposta, traceback ou `repr` de configuração.
- Nenhum teste faz requisição real à Azure.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos.

## Notas técnicas

**Ponto em aberto, que você precisa resolver e reportar.** O SDK expõe `get_analyze_result_pdf` e
`get_analyze_result_figure`, mas não está documentado um método público para buscar o JSON do
resultado por `result_id` — e a rota `GET` precisa exatamente disso. Duas saídas, nesta ordem:

1. `poller.continuation_token()` na submissão e retomada com `continuation_token=` na consulta.
2. `GET` direto no REST com `httpx`:
   `{endpoint}/documentintelligence/documentModels/prebuilt-read/analyzeResults/{resultId}?api-version=2024-11-30`,
   header `Ocp-Apim-Subscription-Key`.

Verifique qual funciona na versão instalada do SDK e **diga no relatório qual escolheu e por quê**.
A porta `ServicoDeOcr` isola a decisão: nenhuma outra camada pode mudar por causa dela.

- O id da operação sai em `poller.details["operation_id"]`.
- A API fica **sem estado**: o id devolvido ao cliente é o do Azure. Não crie banco, cache nem
  dicionário em memória para guardar operações.
- Use o cliente **assíncrono** (`azure.ai.documentintelligence.aio`), injetado, com ciclo de vida
  amarrado ao `lifespan` da aplicação — nada de criar cliente dentro do método.
- A chave é segredo: `SecretStr` no pydantic-settings, e nunca interpolada em mensagem de erro.
- Credenciais reais ainda **não** estão disponíveis. Implemente e teste com mock; se precisar de um
  teste manual contra a Azure, reporte ao `Encefalo` em vez de improvisar.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [ ] **git** (`Cais`) — commits e PR
