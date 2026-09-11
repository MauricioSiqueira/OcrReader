# fix-0005 — Remoção da instrumentação de métricas

**Plano de origem:** docs/plans/plan-0005-remocao-da-instrumentacao-de-metricas.md
**Branch:** fix/0005-remocao-da-instrumentacao-de-metricas

## Objetivo

O projeto volta a não ter instrumentação de métricas, sem deixar nenhum campo, módulo ou teste órfão
para trás.

## Escopo

- [ ] Remover `src/ocr_reader/infrastructure/observabilidade/` por completo, e o diretório de teste
      correspondente.
- [ ] `interfaces/api/aplicacao.py`: remover a chamada a `configurar_log()` e o import.
- [ ] `interfaces/api/rotas/extracoes.py`: remover o logger, as funções `_registrar_*` e as chamadas.
- [ ] `domain/modelos/extracao.py`: remover `MetricasDaExtracao` e o campo `metricas` de
      `ResultadoDaExtracao`.
- [ ] `infrastructure/azure/servico_de_ocr_document_intelligence.py`: remover `_calcular_metricas` e
      seu uso.
- [ ] `application/casos_de_uso/solicitar_extracao_de_texto.py`: remover de `ExtracaoSolicitada` os
      campos `tipo_de_arquivo` e `tamanho_em_bytes`.
- [ ] `application/casos_de_uso/validar_documento_remoto.py`: remover `tamanho_em_bytes` de
      `VeredictoDeValidacao`. **Atenção:** o tamanho continua sendo usado *dentro* da validação para
      comparar com o limite — o que sai é a propagação para fora, não a regra.
- [ ] Remover os testes que existiam só para as métricas e ajustar os que construíam os campos
      removidos.
- [ ] `tests/dubles_de_portas.py` e demais dublês: remover o que ficou sem uso.

## Fora de escopo

- Rota de health check — é a `feat-0006`.
- Qualquer outra mudança de comportamento, de contrato HTTP ou de dependência.
- Remover a regra de limite de tamanho. Ela não é métrica, é validação.

## Critérios de aceite

- `grep -ri "metrica\|observabilidade\|log_estruturado\|configurar_log" src/ tests/` não retorna nada.
- Nenhum import de `logging` sobra em `src/`.
- Os corpos e status das respostas HTTP continuam idênticos aos de hoje.
- A validação continua rejeitando arquivo acima do limite com `413`.
- Nenhum campo removido sobra em construtor, dublê ou teste.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos, sem teste marcado como
  ignorado ou pulado para contornar a remoção.

## Notas técnicas

- Não use `git revert`: você não opera git. Remova o código diretamente.
- A contagem de testes vai cair — é esperado. Diga no relatório quantos ficaram e quais removeu.
- Se encontrar algum campo que **outro** consumidor usa além do log, **não remova**: reporte ao
  `Encefalo` explicando quem usa.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [ ] **git** (`Cais`) — commits e PR
