# plan-0005 — Remoção da instrumentação de métricas

**Estado:** aprovado pelo usuário em 2026-09-11
**Tarefa:** `docs/tasks/fix-0005-remocao-da-instrumentacao-de-metricas.md`
**Desfaz:** `plan-0004` / `feat-0004` (PR #4, mesclada)

## Contexto

A `feat-0004` instrumentou a API com log estruturado para o usuário medir tempo de processamento.
Ele coletou os números de que precisava e a instrumentação cumpriu seu propósito. Mantê-la agora
seria violar o `CLAUDE.md`, que proíbe código morto — daí o prefixo `fix-`: não é remover capacidade
desejada, é corrigir uma violação de convenção que passaria a existir.

## Por que a remoção é maior que "apagar o log"

A `feat-0004` não se limitou ao módulo de observabilidade. Para alimentar os eventos, ela propagou
dados por três camadas:

- `VeredictoDeValidacao` ganhou `tamanho_em_bytes`;
- `ExtracaoSolicitada` ganhou `tipo_de_arquivo` e `tamanho_em_bytes`;
- `ResultadoDaExtracao` ganhou `metricas`, e o domínio ganhou `MetricasDaExtracao`;
- o adaptador ganhou `_calcular_metricas`.

Remover só o módulo de log deixaria todos esses campos sem consumidor — exatamente o código morto
que se quer evitar. A remoção acompanha cada campo até o ponto onde ele deixa de ter uso.

## Critério para o que fica

Um campo só permanece se algo **além do log** o consumir. `tamanho_em_bytes` é usado dentro da
validação para comparar com o limite — esse uso fica; o que sai é a **propagação para fora** dela.

## Risco

Remover campo de dataclass quebra quem os constrói, inclusive testes. O sinal de que a remoção foi
completa e correta é a suíte inteira passando sem nenhum ajuste "de conveniência" que apenas mascare
um campo esquecido.

## Fora de escopo

Qualquer outra mudança de comportamento. O contrato HTTP continua idêntico — como a `feat-0004` não
o alterou, desfazê-la também não altera.
