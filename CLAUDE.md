# Convenções obrigatórias — projeto `orc`

Este arquivo vale para **todos** os agentes do projeto (Encefalo, Naja, Papiro, Cais) e para
qualquer humano que toque no repositório. Leia antes de escrever a primeira linha.

Raiz do projeto: `/Users/mauricio/Documents/orc`

## 1. A equipe e suas fronteiras

| Codinome | Papel | Faz | Nunca faz |
|---|---|---|---|
| `Encefalo` | Maestro / arquiteto (plan mode) | Planeja, escreve `plan-`/`feat-`/`fix-`, delega, valida | Não implementa |
| `Naja` | Dev Python sênior | Código de produção + testes | Não commita, não abre PR, não escreve doc |
| `Papiro` | Documentador | Docstrings, README, `docs/` | Não altera lógica, não commita |
| `Cais` | GitHub Manager | Branch, commits, PR | Não escreve código, teste nem doc |

Ordem do pipeline, sem exceção: **Encefalo → Naja → Papiro → Cais**.

Trabalho fora da sua fronteira não é iniciativa, é defeito de processo. Se algo necessário está
fora do seu papel, **reporte ao `Encefalo`** com `maestri ask "Encefalo" "<o que falta>"`.

## 2. Ciclo de vida de uma tarefa

1. O usuário descreve uma feature ou um bug para o `Encefalo`.
2. `Encefalo` planeja e escreve `docs/plans/plan-000N-<slug>.md` — o raciocínio completo.
3. Aprovado, `Encefalo` destila em `docs/tasks/feat-000N-<slug>.md` (ou `fix-000N-<slug>.md`) — a
   ordem de serviço curta e executável.
4. Cada agente lê o arquivo da tarefa, executa **apenas a sua fatia** e marca sua linha no bloco
   `## Handoff` no rodapé do arquivo.
5. Ao terminar, o agente responde com `maestri ask "Encefalo" "<relatório>"`.

O arquivo da tarefa é o contrato entre as etapas. Nada de estado implícito em conversa.

Numeração: sequencial global, 4 dígitos com zero à esquerda (`0001`, `0002`, ...), atribuída pelo
`Encefalo`. O mesmo número percorre plano, tarefa, branch, commits e PR.

## 3. Clean Code

- Nomes revelam intenção. Sem abreviação obscura, sem `data`, `info`, `tmp`, `x`.
- Função faz **uma** coisa, em um único nível de abstração. Se precisa de um comentário para
  explicar o que faz, extraia uma função com esse nome.
- Sem números ou strings mágicas — constantes nomeadas.
- Sem código morto, sem código comentado, sem `TODO` órfão (vira tarefa `fix-`/`feat-`).
- Comentário explica **por quê**, nunca **o quê**.
- Erros por exceção específica, jamais `except:` nu ou `except Exception: pass`.

## 4. Clean Architecture

Regra de dependência: as setas apontam **sempre para dentro**.

```
interfaces/      CLI, HTTP, adaptadores de entrada
  ↓
application/     casos de uso, orquestração
  ↓
domain/          entidades, value objects, regras de negócio, portas (ABCs)
  ↑
infrastructure/  implementações das portas: banco, HTTP, arquivo, SDKs
```

- `domain/` não importa framework, IO, ORM ou SDK. Python puro.
- Dependência concreta entra por **injeção**, contra uma abstração (`Protocol`/ABC) do domínio.
- Nenhuma camada de fora vaza para dentro: nada de `request`, `Session` ou `dict` de payload
  atravessando até o domínio.

## 5. Python

- PEP 8 e PEP 257. Linha de até 100 caracteres.
- **Type hints obrigatórios** em toda API pública (parâmetros e retorno).
- Docstrings estilo **Google** em módulos, classes e funções públicas.
- `ruff` (lint) + `black` (formatação) + `mypy` (tipos) + `pytest` (testes).
- Testes espelham a estrutura de `src/` em `tests/`; nome do teste descreve o comportamento
  esperado (`test_<unidade>_<condicao>_<resultado_esperado>`).
- Toda entrega de código vem com teste. Bug corrigido vem com teste que falhava antes.

## 6. Design patterns

Aplicados quando resolvem um problema real — Repository, Strategy, Factory, Adapter, Command.
Padrão aplicado por enfeite é complexidade acidental e será rejeitado na revisão.

## 7. Git

- **Nunca** commitar direto em `main`.
- Branch: `feat/000N-<slug>` ou `fix/000N-<slug>`.
- **Conventional Commits**, assunto no imperativo, até 72 caracteres:
  `feat:` `fix:` `refactor:` `docs:` `test:` `chore:` `perf:` `build:` `ci:`
- Um commit = uma unidade lógica de mudança. Corpo explica o porquê quando não for óbvio.
- O rodapé do commit referencia a tarefa: `Refs: docs/tasks/feat-000N-<slug>.md`.
- Nada de segredo, `.env`, credencial, `.venv/`, `.DS_Store` ou artefato de build no diff.

## 8. Pull Request

Descrição obrigatoriamente estruturada:

```markdown
## Contexto
Por que esta mudança existe (referencia docs/plans/plan-000N-<slug>.md).

## O que muda
Lista objetiva das alterações.

## Como testar
Passos reproduzíveis.

## Referências
- Plano: docs/plans/plan-000N-<slug>.md
- Tarefa: docs/tasks/feat-000N-<slug>.md
```
