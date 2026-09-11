# feat-0004 — Métricas de processamento por log estruturado

**Plano de origem:** docs/plans/plan-0004-metricas-por-log-estruturado.md
**Branch:** feat/0004-metricas-por-log-estruturado

## Objetivo

Cada extração passa a emitir uma linha JSON no stdout com a duração do OCR no Azure, o tamanho do
documento e o número de páginas — permitindo calcular métricas de operação sem instrumentar nada
por fora.

## Escopo

- [ ] `domain/modelos/extracao.py`: acrescentar `MetricasDaExtracao` (value object imutável) com
      `duracao_do_ocr_em_ms: int` e `quantidade_de_paginas: int`. Acrescentar a
      `ResultadoDaExtracao` o campo opcional `metricas: MetricasDaExtracao | None = None`,
      preenchido apenas quando a situação é `CONCLUIDA`.
- [ ] `infrastructure/azure/servico_de_ocr_document_intelligence.py`: em
      `_resultado_a_partir_do_corpo`, extrair `createdDateTime` e `lastUpdatedDateTime` (a duração é
      a diferença, em milissegundos) e o número de páginas de `analyzeResult.pages`. Se algum campo
      faltar, `metricas` fica `None` — **nunca** levante exceção por causa de métrica.
- [ ] `infrastructure/observabilidade/log_estruturado.py`: `logging.Formatter` da biblioteca padrão
      emitindo uma linha JSON por registro. **Nenhuma dependência nova.**
- [ ] `interfaces/api/aplicacao.py`: configurar o log na fábrica da aplicação.
- [ ] `interfaces/api/rotas/extracoes.py`: emitir os eventos
      - `extracao_solicitada` no `POST`: `id_extracao`, `tipo_de_arquivo`, `tamanho_em_bytes`;
      - `extracao_concluida` no `GET`, apenas quando `CONCLUIDA` e houver métricas:
        `id_extracao`, `duracao_do_ocr_em_ms`, `quantidade_de_paginas`.
- [ ] Se o `VeredictoDeValidacao` ainda não carrega o tamanho em bytes, acrescentar o campo — o dado
      já existe no `CabecalhoRemoto` lido pela validação, só não é propagado.
- [ ] Testes: formatador produz JSON válido; adaptador calcula a duração corretamente; adaptador com
      campos ausentes devolve `metricas=None` sem quebrar; rotas emitem os eventos com os campos
      esperados (use `caplog`); **e o teste de vazamento descrito abaixo.**

## Fora de escopo

- Tracing distribuído, exportador Prometheus, dashboard, alerta.
- Timeout ou circuit breaker na chamada ao Azure.
- Duração da nossa validação e contagem de rejeições por motivo — não foram pedidas.
- Qualquer mudança no corpo das respostas HTTP. O contrato público não muda.

## Critérios de aceite

- `POST /extracoes` bem-sucedido emite uma linha JSON com `evento=extracao_solicitada`,
  `id_extracao`, `tipo_de_arquivo` e `tamanho_em_bytes`.
- `GET /extracoes/{id}` de extração concluída emite `evento=extracao_concluida` com
  `duracao_do_ocr_em_ms` e `quantidade_de_paginas`.
- Toda linha emitida é JSON válido, parseável por `json.loads`.
- Resposta do Azure sem os campos de data ou sem `pages` não quebra nada: `metricas=None`, sem log
  de métrica, sem exceção, requisição responde normalmente.
- **Nenhum log contém o SAS URI, sua query de assinatura, ou a chave do Document Intelligence.**
  Teste dedicado e obrigatório: dispare as rotas com um SAS URI de teste contendo `sig=`, capture
  todo o log e assegure que nem a assinatura nem a chave aparecem em nenhuma linha.
- O contrato HTTP não muda: os corpos de resposta continuam idênticos aos de hoje.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos.

## Notas técnicas

- **Não crie porta `RegistroDeEventos`.** O plano decidiu contra: nada no domínio decide sobre log,
  e porta sem problema real é padrão decorativo. Os dados saem pelos valores de retorno que já
  existem; a escrita acontece em `interfaces/`.
- `MetricasDaExtracao` é Python puro. O `domain/` continua sem importar `logging`.
- As datas do Azure vêm em ISO 8601 com fuso. Use `datetime.fromisoformat`; atenção ao sufixo `Z`,
  que versões do Python tratam de formas diferentes — teste com o formato real da resposta.
- Métrica nunca pode derrubar requisição. Falha ao calcular métrica é métrica ausente, não erro.
- Log vai para stdout. Não escreva arquivo de log.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [x] **git** (`Cais`) — 4 commits, push, PR #4 aberta
