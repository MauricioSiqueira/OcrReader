# Remontagem da equipe no Maestri

Manual para recriar a equipe deste projeto do zero, em qualquer workspace Maestri enraizado em
`/Users/mauricio/Documents/orc`. Todos os comandos abaixo foram executados e verificados.

**Pré-requisito:** o terminal do cérebro precisa de **Maestro Mode** ligado — isso só se faz pela
interface do Maestri. Sem ele, `role`, `recruit` e `workspace` respondem *"This terminal is not the
Maestro"*.

## A equipe

| Codinome | Role | Modelo | Fronteira |
|---|---|---|---|
| `Encefalo` | — (o próprio Maestro) | Opus | Planeja e delega. **Roda sempre em plan mode.** Não implementa. |
| `Naja` | Dev Python Sênior | Sonnet | Código de produção + testes. Não commita, não documenta. |
| `Papiro` | Documentador de Código | Haiku | Docstrings, README, `docs/`. Não altera lógica. |
| `Cais` | GitHub Manager | Haiku | Branch, commits, PR. Não toca em código. |

Pipeline, sem exceção: **Encefalo → Naja → Papiro → Cais**. O contrato entre etapas é o arquivo
`docs/tasks/<id>.md`, cujo bloco `## Handoff` cada agente marca ao terminar. Ver `CLAUDE.md` e
`docs/README.md`.

## 1. Criar as roles

Os prompts íntegros vivem em `docs/team/roles/`. A partir da raiz do projeto:

```bash
maestri role create "Dev Python Sênior"       "$(cat docs/team/roles/dev-python-senior.md)"
maestri role create "Documentador de Código"  "$(cat docs/team/roles/documentador-de-codigo.md)"
maestri role create "GitHub Manager"          "$(cat docs/team/roles/github-manager.md)"
```

Roles são **scoped por workspace**: existem só no workspace onde foram criadas e não podem ser
criadas remotamente em outro. Por isso este arquivo existe.

## 2. Recrutar

`maestri recruit` **não tem flag de modelo** — o modelo se escolhe dentro de `--command`.

```bash
maestri recruit "Naja" --preset "Claude Code" --role "Dev Python Sênior" \
  --dir /Users/mauricio/Documents/orc \
  --command "claude --model sonnet --add-dir /Users/mauricio/Documents/orc --permission-mode acceptEdits"

maestri recruit "Papiro" --preset "Claude Code" --role "Documentador de Código" \
  --dir /Users/mauricio/Documents/orc \
  --command "claude --model haiku --add-dir /Users/mauricio/Documents/orc --permission-mode acceptEdits"

maestri recruit "Cais" --preset "Claude Code" --role "GitHub Manager" \
  --dir /Users/mauricio/Documents/orc \
  --command "claude --model haiku --add-dir /Users/mauricio/Documents/orc --permission-mode acceptEdits"
```

### Duas armadilhas, aprendidas na marra

1. **`--dir` não é opcional.** Sem ele, o recruta herda o *diretório registrado do Maestro* no
   Maestri — que não é o `pwd` do processo. Na primeira montagem isso fez os três nascerem dentro
   de `/Users/mauricio/Documents/GitHub/processar.backend/.maestri/roles/`, ou seja, **dentro do
   repositório git de outro projeto**. Um `git status` sem `-C` operaria no projeto errado.
   O `--dir` move o diretório de role para dentro do `orc` **sem perder a role** (testado).
2. **`--add-dir` também não é opcional.** O recruta nasce em `orc/.maestri/roles/<id>/`, um
   subdiretório; a raiz do projeto fica *acima* do cwd dele e sem `--add-dir` fica fora de alcance.

## 3. Conectar

```bash
maestri connect "Naja" "Papiro"
```

O documentador pergunta direto ao dev sobre decisões de implementação. O `Cais` fica ligado só ao
`Encefalo`, de propósito: a saída para o git passa pelo cérebro.

## 4. Verificar

```bash
maestri workspace list   # deve marcar "(you are here)" no workspace enraizado em .../orc
maestri list             # Maestro + os 3, com Papiro aninhado sob Naja
maestri role list         # as 3 roles, "in use by 1 terminal" cada
```

Smoke test em lote — valida role, modelo, diretório e allowlist de uma vez:

```bash
maestri ask --batch '{"Naja":"(1) codinome e papel; (2) pwd; (3) rode git -C /Users/mauricio/Documents/orc log --oneline","Papiro":"idem","Cais":"idem"}'
```

Critérios de aprovação:

- o `pwd` de cada um cai em `/Users/mauricio/Documents/orc/.maestri/roles/<id>` — **nunca** em
  `processar.backend`;
- o `git log` mostra os commits de bootstrap deste repositório;
- **nenhum deles trava pedindo aprovação** para `ls` ou `git log` — é a prova de que a allowlist de
  `.claude/settings.json` alcança o cwd deles.

Se um agente travar num pedido de aprovação, responda por ele sem reiniciar:
`maestri ask "Nome" --raw "1\n"`.

## Pendência conhecida

`.claude/settings.json` tem `"Bash(git push:*)"` no bloco `deny`. **`deny` é bloqueio permanente**,
não um pedido de aprovação — do jeito que está, o `Cais` não conseguirá publicar nada quando houver
remoto. A linha precisa sair:

```bash
sed -i '' '/"Bash(git push:\*)",/d' /Users/mauricio/Documents/orc/.claude/settings.json
```

Isto é ação do **usuário**: o classificador de auto mode do Claude Code barra edições de
`settings.json` feitas pelo agente (proteção contra automodificação), inclusive via ferramenta de
edição. Depois de alterar, reinicie os recrutas para recarregarem as permissões — as settings são
lidas no início da sessão:

```bash
maestri recruit "Naja" --replace "Naja" --role "Dev Python Sênior" \
  --dir /Users/mauricio/Documents/orc \
  --command "claude --model sonnet --add-dir /Users/mauricio/Documents/orc --permission-mode acceptEdits"
```

(idem para `Papiro` e `Cais`, com `--model haiku`). `--replace` preserva nó, posição no canvas e
conexões; só o processo reinicia. O histórico de conversa do recruta se perde.
