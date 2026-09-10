# AI Technical Knowledge Assistant

Laboratório incremental de AI Engineering em Python. Objetivo final: consultar documentação
própria com RAG, interpretar consultas com NLP e executar ferramentas via MCP e um agente.

## Sessão atual: Fases 0 e 1

Estrutura do projeto e chat local implementados, sem frameworks de orquestração.
O fluxo atual é: **terminal → Python → HTTP /api/chat → Ollama → LLM → resposta**.
Não há busca em documentos, fontes verificadas, NLP, API REST ou execução de ferramentas ainda.

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

### Verificação

Execute no shell, fora do chat, com o ambiente virtual ativo:

```sh
python -m pytest -q
```

Os testes usam HTTP simulado: verificam histórico, limpeza, limites, configuração inválida
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
| 2 | NLP independente | Planejada |
| 3 | Ingestion TXT, Markdown e PDF | Planejada |
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

SQLite já integra a biblioteca padrão do Python. FastAPI, ChromaDB,
sentence-transformers e spaCy serão instalados quando suas fases começarem.
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
