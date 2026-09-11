# Processo de trabalho

Índice do que vive aqui e de como uma ideia vira commit.

## Estrutura

```
docs/
  plans/plan-000N-<slug>.md   # o raciocínio: contexto, decisões, alternativas, riscos
  tasks/feat-000N-<slug>.md   # a ordem de serviço: escopo fechado, executável
  tasks/fix-000N-<slug>.md
```

- **`plan-`** é escrito pelo `Encefalo` com o usuário. Pode ser longo. É onde a decisão mora.
- **`feat-`/`fix-`** é a destilação do plano para quem executa. Curto, imperativo, sem ambiguidade.
- A numeração é **sequencial global**: o `0007` é o sétimo item do projeto, seja feat ou fix, e o
  mesmo número atravessa plano, tarefa, branch, commits e PR.

## Ciclo de vida

```
usuário descreve
   ↓
Encefalo  → docs/plans/plan-000N-<slug>.md    (aprovado pelo usuário)
   ↓
Encefalo  → docs/tasks/feat-000N-<slug>.md    (ordem de serviço)
   ↓
Naja      → implementa + testes                → Handoff [x] dev
   ↓
Papiro    → docstrings, README, docs/          → Handoff [x] docs
   ↓
Cais      → branch, commits, PR                → Handoff [x] git
   ↓
Encefalo  → confere e reporta ao usuário
```

Cada agente lê o arquivo da tarefa antes de agir e marca sua linha no `## Handoff` ao terminar.
O arquivo é o contrato: se não está escrito lá, não está no escopo.

## Modelo de arquivo de tarefa

```markdown
# feat-000N — <título>

**Plano de origem:** docs/plans/plan-000N-<slug>.md
**Branch:** feat/000N-<slug>

## Objetivo
Uma frase: o que passa a ser possível depois desta entrega.

## Escopo
- [ ] item executável e verificável
- [ ] ...

## Fora de escopo
- o que explicitamente NÃO deve ser feito agora

## Critérios de aceite
- comportamento observável 1
- comportamento observável 2

## Notas técnicas
Arquivos a tocar, padrões a seguir, armadilhas conhecidas.

## Handoff
- [ ] **dev** (`Naja`) — implementação + testes
- [ ] **docs** (`Papiro`) — docstrings e documentação
- [ ] **git** (`Cais`) — commits e PR
```
