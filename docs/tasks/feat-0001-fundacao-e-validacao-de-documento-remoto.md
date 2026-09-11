# feat-0001 — Fundação do projeto e validação de documento remoto

**Plano de origem:** docs/plans/plan-0001-api-ocr-document-intelligence.md
**Branch:** feat/0001-fundacao-e-validacao-de-documento-remoto

## Objetivo

A API passa a receber um SAS URI de blob da Azure, ler apenas o cabeçalho do arquivo e responder se
o tipo é aceito — sem baixar o arquivo inteiro e sem ainda chamar o Document Intelligence.

## Escopo

- [ ] `pyproject.toml` com `uv`, Python 3.12, `fastapi`, `uvicorn`, `httpx`, `python-magic`,
      `pydantic-settings`; grupo de desenvolvimento com `ruff`, `black`, `mypy`, `pytest`,
      `pytest-asyncio`. Linha de 100 caracteres no `ruff` e no `black`; `mypy` em modo estrito.
- [ ] Estrutura `src/ocr_reader/{domain,application,infrastructure,interfaces}` conforme o plano.
- [ ] `domain/modelos/tipo_de_arquivo.py`: enum `TipoDeArquivo` com PDF, DOCX, XLSX, PPTX, HTML,
      JPEG, PNG, BMP, TIFF e HEIF, e o catálogo de MIME types correspondente.
- [ ] `domain/modelos/endereco_de_blob.py`: value object imutável que só existe se o URI for `https`,
      tiver host na allowlist e trouxer query de assinatura. Rejeição vira exceção específica.
- [ ] `domain/portas/leitor_de_bytes_remotos.py` e `domain/portas/detector_de_tipo_de_arquivo.py`
      como `Protocol`.
- [ ] `domain/erros.py`: `EnderecoInvalido`, `TipoDeArquivoNaoSuportado`, `ArquivoExcedeLimite`,
      `DocumentoInacessivel`. Nada de `except` nu em lugar nenhum.
- [ ] `infrastructure/http/leitor_de_bytes_httpx.py`: `httpx.AsyncClient` com `Range: bytes=0-N`,
      extraindo o tamanho total do `Content-Range`. Cliente injetado, não criado dentro do método.
- [ ] `infrastructure/deteccao/detector_libmagic.py`: detecção por magic bytes. Se voltar ZIP
      genérico, relê com janela de 512 KiB e redetecta uma única vez antes de desistir.
- [ ] `infrastructure/configuracao.py` com `pydantic-settings`: allowlist de hosts, tamanho máximo
      (padrão 500 MB), janela de cabeçalho (padrão 8 KiB), janela ampliada, timeouts.
- [ ] `application/casos_de_uso/validar_documento_remoto.py`: orquestra endereço → cabeçalho →
      detecção → veredito. Um nível de abstração, sem IO direto.
- [ ] `interfaces/api/`: fábrica da aplicação, rota `POST /extracoes`, DTOs pydantic, injeção das
      portas e tradutor de erro de domínio para status HTTP.
- [ ] Testes `pytest` espelhando `src/` em `tests/`, incluindo fixtures binárias mínimas de PDF,
      DOCX, XLSX, PNG, JPEG e de um ZIP comum que deve ser rejeitado.

## Fora de escopo

- Qualquer chamada ao Azure Document Intelligence — é a `feat-0002`.
- `GET /extracoes/{id}`, resposta `202` e id de extração — `feat-0002`.
- Autenticação da API, rate limiting, persistência, Docker, CI.
- Qualquer motor de OCR local (Tesseract, PaddleOCR, EasyOCR). Proibido, agora e depois.

## Critérios de aceite

- `POST /extracoes` com SAS URI de PDF válido responde `200` com o tipo detectado.
- URI com host fora da allowlist responde `400` e **não** faz nenhuma requisição de rede.
- Arquivo de tipo não aceito (ex.: executável, ZIP comum) responde `415`.
- Arquivo acima do limite configurado responde `413`, detectado pelo `Content-Range`, sem baixar o
  corpo.
- Blob inacessível ou SAS expirado responde `502`, sem vazar o URI na mensagem.
- Nenhuma resposta, log ou traceback contém o SAS URI ou sua query de assinatura.
- `ruff check`, `black --check`, `mypy src` e `pytest` passam limpos.

## Notas técnicas

- A leitura do cabeçalho é o único IO desta tarefa: nunca carregue o arquivo inteiro em memória nem
  em disco.
- O host da allowlist entra por configuração; o padrão é `*.blob.core.windows.net`. Esta é a barreira
  contra SSRF — trate como requisito de segurança, não como validação de conveniência.
- `python-magic` depende da biblioteca nativa `libmagic`. Se ela não estiver instalada, **pare e
  reporte ao `Encefalo`** em vez de trocar por outra biblioteca por conta própria.
- Nomenclatura de domínio em português; bibliotecas externas mantêm seus nomes originais.
- Se alguma ferramenta de qualidade não estiver disponível, diga isso no relatório em vez de pular a
  verificação em silêncio.

## Handoff

- [x] **dev** (`Naja`) — implementação + testes
- [x] **docs** (`Papiro`) — docstrings e documentação
- [ ] **git** (`Cais`) — commits e PR
