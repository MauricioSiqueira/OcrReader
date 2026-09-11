# feat-0003 — Configuração por arquivo `.env`

**Plano de origem:** docs/plans/plan-0003-configuracao-por-arquivo-env.md
**Branch:** feat/0003-configuracao-por-arquivo-env

## Objetivo

A configuração passa a ser lida de um arquivo `.env` na raiz do projeto, eliminando a necessidade de
repetir `export` a cada sessão de terminal — sem que o segredo entre no repositório.

## Escopo

- [ ] Acrescentar `env_file=".env"` e `env_file_encoding="utf-8"` ao `SettingsConfigDict` de
      `src/ocr_reader/infrastructure/configuracao.py`. Nenhuma outra mudança no arquivo.
- [ ] Criar `.env.example` na raiz, versionado, listando **todas** as nove variáveis com valores de
      exemplo e um comentário curto em cada. A chave e o endpoint recebem placeholder óbvio, jamais
      valor real.
- [ ] Testes em `tests/infrastructure/test_configuracao.py`:
      - lê valores de um `.env` temporário;
      - variável de ambiente real **sobrescreve** o valor vindo do `.env`;
      - ausência de `.env` mantém os padrões, sem erro;
      - `repr` e `str` da `Configuracao` não revelam a chave.

## Fora de escopo

- Múltiplos arquivos por perfil (`.env.dev`, `.env.prod`).
- Integração com Key Vault ou qualquer cofre de segredo.
- Qualquer mudança em domínio, aplicação ou interfaces.
- Criar um `.env` de verdade — isso é ação do usuário, na máquina dele.

## Critérios de aceite

- Com um `.env` na raiz contendo `OCR_READER_ENDPOINT_DO_DOCUMENT_INTELLIGENCE=...`, a aplicação
  sobe lendo esse valor sem nenhum `export`.
- Exportar a mesma variável no ambiente sobrescreve o que está no `.env`.
- Sem `.env`, tudo continua funcionando com os padrões — nenhum teste existente quebra.
- `.env.example` lista as nove variáveis e não contém segredo.
- `git status` não mostra `.env` como arquivo novo a ser versionado.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos.

## Notas técnicas

- O caminho do `env_file` é resolvido em relação ao diretório de trabalho do processo. Leve isso em
  conta nos testes: use `tmp_path` e `monkeypatch.chdir`, não caminho absoluto fixo.
- Não mexa na ordem dos campos nem nos valores padrão existentes.
- A chave permanece `SecretStr`. O teste de não vazamento é obrigatório, não opcional.
- **Não crie um arquivo `.env`** no repositório, nem para testar. Use `tmp_path`.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [x] **git** (`Cais`) — 3 commits, push, PR #3 aberta
