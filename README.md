# AI Technical Knowledge Assistant

Laboratório incremental de AI Engineering em Python. Objetivo final: consultar documentação
própria com RAG, interpretar consultas com NLP e executar ferramentas via MCP e um agente.

## Sessão atual: Fases 0 a 3

Estrutura do projeto e chat local implementados, sem frameworks de orquestração.
O fluxo atual é: **terminal → Python → HTTP /api/chat → Ollama → LLM → resposta**.
O NLP e a ingestão agora têm CLIs independentes. O chat ainda não consulta esses
pipelines: não há busca semântica, RAG, API REST ou execução de ferramentas.

### Iniciar o chat no Mac (ambiente já configurado)

No terminal, execute:

```sh
cd "/Users/leandropinheiroleite/Desktop/AI-Technical_Knowledge-Assistant"
source .venv/bin/activate
python main.py
```

O caminho acima é o deste Mac; ajuste se clonar o projeto em outra pasta.
Quando aparecer `>`, o chat está aguardando uma pergunta. Digite apenas o texto
da pergunta e pressione **Enter**:

```text
Explique o que é uma APDU em até cinco frases.
```

Espere a resposta terminar. Para testar o histórico, digite em seguida:

```text
Agora explique para um iniciante usando uma analogia.
```

Não copie os símbolos `%`, `>` ou `(.venv)`: eles são indicadores do terminal.
Enquanto o chat estiver aberto, o texto digitado será enviado ao assistente.
Para executar comandos como `python`, `ollama` ou `deactivate`, saia primeiro com `/exit`.

| Dentro do chat | Ação |
| --- | --- |
| Uma pergunta + Enter | Envia a pergunta ao modelo |
| `/clear` | Limpa o histórico e mantém o chat aberto |
| `/exit` | Encerra o chat e volta ao shell |
| Ctrl+C ou Ctrl+D | Encerra o chat |

Depois de sair, use `python main.py` para abrir o chat novamente.
Ao terminar a sessão, desative o ambiente virtual no shell:

```sh
deactivate
```

### Configuração inicial (apenas na primeira vez)

Pré-requisitos: Python 3.12+ e [Ollama](https://ollama.com/download/mac).

```sh
# Na raiz do repositório; neste Mac o Python 3.12 está no Homebrew.
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
```

Inicie o aplicativo Ollama ou execute, em outro terminal:

```sh
ollama serve
```

Se o servidor já estiver rodando, não é necessário iniciá-lo novamente.

```sh
ollama pull qwen2.5:3b
python main.py
```

O modelo já estava instalado no ambiente desta sessão. O [qwen2.5:3b](https://ollama.com/library/qwen2.5:3b)
tem aproximadamente 1,9 GB de download e suporte a português. O consumo em execução
é maior que o arquivo do modelo e depende do contexto. Começamos com 4096 tokens
de contexto e no máximo 512 tokens gerados para manter o experimento leve.

Para uma pergunta isolada:

```sh
python main.py --question "Explique o que é uma APDU em até cinco frases."
```

Use `/clear` para limpar o histórico e `/exit`, Ctrl+C ou Ctrl+D para sair.
As conversas ficam somente na memória do processo. O cliente reenvia no máximo quatro
turnos anteriores mais a pergunta atual e o system prompt. Esse limite por turnos não
garante que tudo caiba em tokens: use mensagens curtas nesta fase, pois o Ollama pode
truncar contexto excedente. Não há streaming; a resposta aparece ao terminar.

### Entender a primeira implementação

- **LLM:** modelo que gera texto prevendo tokens a partir da entrada.
- **Tokens:** unidades de texto; não correspondem necessariamente a palavras.
  O CLI mostra as contagens reportadas pelo Ollama.
- **Contexto:** instruções e mensagens disponíveis para a geração atual. É limitado.
- **System prompt:** orienta o comportamento geral; está em `SYSTEM_PROMPT`.
- **User prompt:** pergunta enviada pelo usuário.
- **Inferência:** execução do modelo para produzir a resposta.
- **Temperature:** controla a aleatoriedade da geração; valores maiores tendem a variar mais.
  Temperatura baixa não garante precisão.
- **Hallucination:** resposta plausível, mas incorreta ou sem apoio factual. Um prompt
  pedindo honestidade não elimina esse problema.

O código em `app/llm/llm_client.py` monta explicitamente o JSON enviado à
[API de chat do Ollama](https://docs.ollama.com/api/chat). `main.py` cuida da interação.

### Experimento de EMV: pergunta e contexto

Com o chat aberto, envie cada bloco separadamente e aguarde a resposta:

```text
o que é emv
```

Limpe o histórico para comparar a próxima formulação sem influência da anterior:

```text
/clear
```

```text
No contexto de cartões com chip e terminais de pagamento, o que significa EMV e para que serve? Responda em até cinco frases.
```

Agora mantenha o histórico e envie:

```text
Agora explique isso para um iniciante usando uma analogia, em até três frases.
```

Observe se a resposta fica mais relevante com o domínio explícito e se “isso” é
interpretado pelo histórico. Nos primeiros testes, o contexto melhorou a relevância,
mas ainda houve imprecisões. Respostas fluentes não garantem precisão; nesta fase,
o modelo não realiza buscas, mesmo que diga que procurou referências.

### Experimentos antes da Fase 2

1. Pergunte “Explique o que é uma APDU em até cinco frases”.
2. Pergunte “Agora explique para um iniciante usando uma analogia”.
   Observe como o histórico permite relacionar as perguntas.
3. Execute `/clear` e repita a segunda pergunta. Compare a perda de contexto.
4. Reinicie com `TEMPERATURE=0.8 python main.py` e repita a primeira pergunta
   algumas vezes, limpando o histórico. Compare com o padrão 0.2.
5. Experimente `SYSTEM_PROMPT="Responda em português, sempre em três tópicos." python main.py`.
6. Pergunte “Qual configuração está no meu arquivo terminal-1002.conf?”.
   Observe se o modelo admite que não tem acesso ao arquivo. Não considere uma
   resposta específica como evidência de leitura.

Registre pergunta, configuração, resposta e observações. Analise precisão, clareza,
obediência ao formato e incerteza. Só então avance para o NLP.
Variáveis do terminal prevalecem sobre o arquivo `.env`.

Para os experimentos de configuração, saia do chat com `/exit` e execute
**um comando por vez no shell**, com o ambiente virtual ativo:

```sh
TEMPERATURE=0.2 python main.py
```

```sh
TEMPERATURE=0.8 python main.py
```

```sh
SYSTEM_PROMPT="Responda em português, sempre em três tópicos." python main.py
```

Esses valores valem apenas para a execução daquele comando. Para voltar à
configuração do `.env` (ou aos padrões, se ele não existir), execute `python main.py`
sem os prefixos, desde que não haja variáveis exportadas no shell.


### Fase 2 — NLP independente do LLM

No shell, fora do chat, atualize as dependências:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Execute:

```sh
python -m app.nlp.nlp_pipeline "Analise os erros Visa do terminal 1002"
```

Resultado esperado:

```json
{
  "intent": "analyze_error",
  "entities": {"brand": "VISA", "terminal": "1002"},
  "keywords": ["erro", "visa", "terminal"]
}
```

Para observar tokenização e normalização:

```sh
python -m app.nlp.nlp_pipeline "Busque documentação sobre APDU" --details
python -m app.nlp.nlp_pipeline "O que é EMV?"
```

O pipeline usa o tokenizador português do spaCy, stop words e reconhecimento
de entidades por regras com [EntityRuler](https://spacy.io/api/entityruler).
Não requer baixar um modelo estatístico nem iniciar Ollama. A normalização
remove acentos e converte para minúsculas nas comparações e palavras-chave;
um pequeno dicionário trata plurais de domínio. Isso não é lematização completa.

As intenções são `explain_concept`, `analyze_error`, `search_docs` e `unknown`,
nessa prioridade. Reconhecemos VISA, Mastercard, Elo, Amex/American Express e
a expressão “terminal” seguida de dígitos, preservando zeros iniciais.
Múltiplas entidades do mesmo tipo viram listas; uma ocorrência retorna uma string.
As regras não compreendem negações, ambiguidade ou todas as formas de escrever uma
intenção. Por exemplo, “não analise os erros” ainda pode ser classificado como
`analyze_error`. Nenhuma ação é executada com essa classificação.

Para comparar NLP tradicional com LLM, envie a mesma entrada ao chat:

```sh
python main.py --question 'Extraia intent, entities e keywords como JSON desta consulta: Analise os erros Visa do terminal 1002'
```

Compare formato, repetibilidade, tempo e cobertura de variações. O resultado do
LLM não é validado automaticamente como JSON nesta fase.

### Fase 3 — Document ingestion

Coloque documentos próprios em `documents/linux/`, `documents/cpp/`,
`documents/emv/`, `documents/iso8583/` ou `documents/api/`.
Há um Markdown fictício em `documents/linux/laboratorio.md` para experimentar.

No shell, execute:

```sh
python -m ingestion.pipeline
```

O comando percorre subpastas e grava `data/chunks.jsonl`, com um objeto JSON
por linha. Para ver o primeiro chunk:

```sh
python -c 'import json; from pathlib import Path; print(json.dumps(json.loads(Path("data/chunks.jsonl").read_text(encoding="utf-8").splitlines()[0]), ensure_ascii=False, indent=2))'
```

Para observar mais divisões e sobreposição:

```sh
python -m ingestion.pipeline --chunk-size 300 --overlap 50
```

Para usar outra pasta e saída:

```sh
python -m ingestion.pipeline --documents documents --output data/experimento.jsonl
```

O fluxo é **arquivo → extração por página → limpeza → janelas de caracteres →
metadados → JSONL**. Cada registro contém `id`, `text` e `metadata`:

- `source`: caminho relativo à pasta de entrada, como `linux/laboratorio.md`.
- `page`: página física do PDF, começando em 1; `null` para TXT/Markdown.
- `category`: primeira subpasta em maiúsculas, ou `GENERAL` para arquivos na raiz.
- `chunk_index`: índice começando em zero, reiniciado a cada página.
- `start_char` e `end_char`: intervalo no texto limpo da página; fim exclusivo.

O tamanho padrão é 800 caracteres, com 120 de sobreposição. São caracteres,
não tokens; as janelas podem cortar palavras ou blocos de código e não atravessam
páginas. A limpeza preserva acentos, indentação e marcação Markdown, normaliza
quebras de linha e reduz linhas vazias repetidas. Não interpreta tabelas ou HTML.

Os IDs são hashes determinísticos do conteúdo e dos metadados. Reexecutar substitui
o JSONL, sem acrescentar duplicatas; mudar texto, caminho ou divisão muda os IDs.
A saída deve ficar fora da pasta de documentos. Um erro de leitura interrompe o
lote e mantém uma saída anterior intacta. A gravação usa substituição atômica.
Arquivos de outras extensões são ignorados; links para fora da raiz são rejeitados.

TXT e Markdown devem estar em UTF-8. PDF usa
[pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html):
PDFs protegidos são rejeitados e páginas sem texto produzem avisos.
Não há OCR; PDFs escaneados podem exigir processamento prévio. A ordem de leitura
de PDFs com colunas e tabelas pode precisar de revisão manual.
Este primeiro pipeline mantém o lote em memória: use documentos pequenos no laboratório.

Depois de inspecionar o JSONL, a próxima fase será transformar esses textos em
embeddings. O arquivo gerado ainda não é consultado pelo chat.

### Verificação

Execute no shell, fora do chat, com o ambiente virtual ativo:

```sh
python -m pytest -q
```

Os testes de NLP cobrem intenções, entidades e variações da consulta. Os de ingestão
cobrem extração real de PDF gerado no teste, metadados, sobreposição, IDs,
arquivos inválidos e gravação JSONL.

Os testes do chat usam HTTP simulado: verificam histórico, limpeza, limites, configuração inválida
e recuperação de falhas. A pergunta isolada acima verifica a integração real com o Ollama.
O teste de integração não comprova a precisão técnica das respostas.

### Estrutura e sequência

```text
app/           api, llm, nlp, rag, embeddings, agents
ingestion/     loaders, parsers, chunking
mcp_server/    tools, resources
documents/     documentação de entrada
data/          bancos e dados gerados (ignorados pelo Git)
tests/         testes automatizados
```

| Fase | Entrega | Situação |
| --- | --- | --- |
| 0 | Estrutura, ambiente e aplicação mínima | Implementada |
| 1 | Cliente Ollama e chat CLI | Implementada; experimentos do usuário em andamento |
| 2 | NLP independente | Implementada; experimentos disponíveis |
| 3 | Ingestion TXT, Markdown e PDF | Implementada; inspeção de chunks disponível |
| 4 | Embeddings e similaridade | Planejada |
| 5 | Busca semântica com ChromaDB | Planejada |
| 6 | Primeiro RAG com fontes | Planejada |
| 7 | Benchmark de retrieval e respostas | Planejada |
| 8 | Advanced RAG incremental | Planejada |
| 9 | REST API com FastAPI | Planejada |
| 10 | MCP Server próprio | Planejada |
| 11 | Agente com ferramentas | Planejada |
| 12 | Interface simples | Planejada |
| 13 | Docker e CI/CD completos | Planejada |

SQLite já integra a biblioteca padrão do Python. spaCy e pypdf foram adicionados
nas Fases 2 e 3. FastAPI, ChromaDB e sentence-transformers serão instalados
quando suas fases começarem.
O Git local já possui remote `origin`; esta sessão não publica alterações no GitHub.

### Docker: base para depois

O Dockerfile inicial executa apenas o CLI; a integração completa fica para a Fase 13.
Docker não estava disponível neste ambiente, portanto o build ainda não foi validado.
Com Docker Desktop instalado no Mac e Ollama rodando no host:

```sh
docker build -t ai-tech-assistant .
docker run --rm -it --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 ai-tech-assistant
```

A conexão depende de o Ollama no host estar acessível ao Docker. O caminho recomendado
para esta sessão é executar Python diretamente no Mac.
