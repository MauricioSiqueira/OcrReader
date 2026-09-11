# plan-0003 — Configuração por arquivo `.env`

**Estado:** aprovado pelo usuário em 2026-09-11
**Tarefa:** `docs/tasks/feat-0003-configuracao-por-arquivo-env.md`

## Contexto

A `Configuracao` declara `SettingsConfigDict(env_prefix="OCR_READER_")` e nada mais. Sem `env_file`,
o pydantic-settings lê **apenas** variáveis de ambiente do processo: um arquivo `.env` na raiz é
silenciosamente ignorado.

Na prática isso obriga o usuário a repetir `export` a cada nova sessão de terminal para as nove
variáveis — e duas delas (endpoint e chave do Document Intelligence) são necessárias em toda
execução com OCR real. O atrito é grande o bastante para empurrar a pessoa ao pior caminho:
escrever a chave direto no `configuracao.py`, que é versionado, e vazá-la no próximo commit.

## Decisão

Acrescentar `env_file=".env"` ao `SettingsConfigDict`. O `.gitignore` já cobre `.env` e `.env.*`
(linhas 26 e 27), então o arquivo real nunca entra no repositório.

Um `.env.example`, esse sim versionado, documenta as chaves com valores de exemplo. É o par
canônico: o `.example` ensina o formato, o `.env` guarda o segredo e nunca sai da máquina.

## Precedência

Variável de ambiente real **vence** o `.env`. É o comportamento padrão do pydantic-settings e o
correto para produção: em container ou CI, a configuração chega pelo ambiente e não pode ser
sobrescrita por um arquivo esquecido na imagem. Precisa estar coberto por teste, porque é o tipo de
detalhe que quebra em silêncio numa atualização de biblioteca.

## Risco

O único risco real é o `.env` verdadeiro escapar para o repositório. Mitigado por três camadas: o
`.gitignore` já existente, o `Cais` conferindo o diff antes de commitar, e um teste que garante que
a chave não aparece em `repr` nem em log.

## Fora de escopo

Suporte a múltiplos arquivos de ambiente por perfil (`.env.dev`, `.env.prod`), carregamento de
segredo por cofre (Key Vault) e qualquer mudança nas demais camadas.
