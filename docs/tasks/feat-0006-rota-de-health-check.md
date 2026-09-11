# feat-0006 — Rota de health check

**Plano de origem:** docs/plans/plan-0006-rota-de-health-check.md
**Branch:** feat/0006-rota-de-health-check
**Depende de:** `fix-0005` integrada

## Objetivo

Um orquestrador passa a conseguir verificar se o processo está vivo e atendendo, sem tocar em
nenhuma dependência externa.

## Escopo

- [ ] `src/ocr_reader/interfaces/api/rotas/saude.py`: rota `GET /health` respondendo `200` com
      `{"situacao": "ok"}`.
- [ ] DTO de resposta em `esquemas.py`, seguindo o padrão dos existentes.
- [ ] Registrar o roteador na fábrica da aplicação.
- [ ] Teste: `GET /health` responde `200` com o corpo esperado.
- [ ] Teste: a rota **não** depende de configuração do Azure — responde `200` mesmo com endpoint e
      chave vazios.

## Fora de escopo

- Qualquer verificação de dependência externa: nada de chamar o Document Intelligence, nada de
  checar rede, nada de readiness.
- Versão da aplicação, uptime, contadores ou qualquer dado além da situação.
- Autenticação na rota.
- Mudança nas rotas de extração.

## Critérios de aceite

- `GET /health` responde `200` com `{"situacao": "ok"}`.
- A rota responde `200` com a configuração do Azure vazia — prova de que não depende dela.
- A rota aparece no OpenAPI (`/docs`).
- Nenhuma rota existente muda de comportamento.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos.

## Notas técnicas

- Liveness responde uma pergunta só: *este processo consegue atender uma requisição?* Se você sentir
  vontade de checar o Azure aqui, **pare e me reporte** — foi decidido contra, e o motivo está no
  plano: instabilidade momentânea da dependência faria o orquestrador reiniciar processos
  saudáveis.
- A rota é trivial de propósito. Não introduza abstração, caso de uso ou porta para ela: não há
  regra de negócio envolvida, e camada sem conteúdo é complexidade acidental.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [x] **git** (`Cais`) — 3 commits, push, PR #6 aberta
