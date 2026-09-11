# plan-0004 — Métricas de processamento por log estruturado

**Estado:** aprovado pelo usuário em 2026-09-11
**Tarefa:** `docs/tasks/feat-0004-metricas-por-log-estruturado.md`

## Contexto

O usuário precisa medir quanto tempo o OCR leva, para calcular métricas de operação. Hoje isso é
impossível: **a aplicação não emite nenhum log**. Não há `logging` em lugar algum de `src/`.

Duas descobertas guiaram o desenho:

1. **O Azure já entrega a duração, e nós a descartamos.** A resposta de `analyzeResults` traz
   `createdDateTime` e `lastUpdatedDateTime`; `_resultado_a_partir_do_corpo` lê apenas o `status`.
   A duração exata do processamento está disponível sem guardar estado nenhum — o que preserva a
   decisão de API sem estado tomada no `plan-0001`.
2. **Duração isolada não é métrica.** Três segundos é ótimo para um documento de 50 páginas e
   péssimo para um de uma. Por isso tamanho e número de páginas entram junto: são o denominador.

## Decisões tomadas com o usuário

| Decisão | Escolha | Descartado |
|---|---|---|
| Destino | Log estruturado em JSON no stdout | Corpo da resposta (amplia contrato público); endpoint Prometheus (dependência nova, perde detalhe por requisição) |
| O que medir | Duração do OCR no Azure + tamanho e páginas | Duração da nossa validação; contagem de rejeições por motivo |
| Timeout na chamada ao Azure | Não agora | Fixar teto antes de ter dados seria chute |

## Onde o log vive, sem furar a arquitetura

Log é IO, e IO não entra no `domain/`. Mas isso **não** exige criar uma porta: o caminho mais simples
que respeita a regra de dependência é deixar os dados fluírem para fora pelos valores de retorno que
já existem, e fazer a escrita na camada mais externa.

- O `domain/` ganha `MetricasDaExtracao`, um value object puro (duração em milissegundos, número de
  páginas). Nenhum import de `logging`.
- O adaptador do Azure, que já traduz o JSON da resposta, passa a extrair também esses campos.
- A camada `interfaces/` — que é onde o IO já mora — escreve a linha de log.

Uma porta `RegistroDeEventos` seria padrão decorativo aqui: nada no domínio precisa decidir sobre
log, e `CLAUDE.md` rejeita padrão sem problema real por trás.

## Formato

Uma linha JSON por evento no stdout, sem dependência nova — `logging.Formatter` da biblioteca padrão
é suficiente. Dependência de formatação de log não se justifica para emitir um dicionário.

Campos: `evento`, `id_extracao`, `tipo_de_arquivo`, `tamanho_em_bytes`, `duracao_do_ocr_em_ms`,
`quantidade_de_paginas`.

## Risco, e é o de sempre

**O SAS URI e a chave da Azure não podem aparecer no log.** Um log estruturado é justamente o lugar
onde credencial vaza sem ninguém notar, porque vai para agregador, é indexado e fica retido. Isso
vira critério de aceite com teste dedicado, não um cuidado implícito.

## Fora de escopo

Tracing distribuído, correlação entre serviços, exportador Prometheus, dashboard, alerta, retenção,
timeout ou circuit breaker na chamada ao Azure, e as duas métricas que o usuário não pediu (duração
da nossa validação e contagem de rejeições por motivo).
