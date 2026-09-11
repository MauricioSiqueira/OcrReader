# plan-0006 — Rota de health check

**Estado:** aprovado pelo usuário em 2026-09-11
**Tarefa:** `docs/tasks/feat-0006-rota-de-health-check.md`
**Depende de:** `fix-0005` (a remoção da instrumentação toca os mesmos arquivos)

## Contexto

A API não tem como um orquestrador saber se está viva. Sem isso, Kubernetes, App Service ou qualquer
balanceador não consegue decidir se deve reiniciar o processo ou tirá-lo do balanceamento.

## Decisões tomadas com o usuário

| Decisão | Escolha | Descartado |
|---|---|---|
| Profundidade | Apenas liveness | Readiness do Azure: cada sondagem gastaria cota do tier F0 e poderia falhar por rede, derrubando um processo saudável |
| Caminho | `/health` | `/saude`, mais coerente com o português do projeto; `/healthz`, do mundo Kubernetes |

O `/health` vence a coerência de idioma por um motivo prático: é o caminho que ferramenta de
infraestrutura sonda por padrão, e um nome inesperado vira configuração extra em todo lugar que
monitora.

## A armadilha que o desenho evita

Health check que consulta dependência externa é uma das formas clássicas de derrubar um sistema
saudável: uma instabilidade momentânea no Azure faria o orquestrador reiniciar processos que estão
perfeitamente funcionais, e o reinício em massa piora a situação em vez de melhorar.

Liveness responde uma pergunta só: *este processo consegue atender uma requisição?* Se a resposta é
sim, reiniciá-lo não ajuda ninguém.

## Fora de escopo

Readiness, sondagem de dependência, métrica de uptime, versão da aplicação no corpo da resposta, e
qualquer mudança nas rotas de extração.
