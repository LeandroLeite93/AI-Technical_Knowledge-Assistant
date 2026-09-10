# Fase 1 — primeiro resultado observado

Ambiente: Python 3.12.14, Ollama 0.33.3, qwen2.5:3b, Apple Silicon,
16 GiB de memória reportados pelo sistema.

Validação: 12 testes automatizados passaram; pip check sem conflitos.
Docker indisponível, build não executado.

Pergunta: “Explique o que é uma APDU em até cinco frases.”

Configuração padrão: temperature=0.2, num_ctx=4096, num_predict=512.

Resposta real do modelo:

> APDU é um Acronym que significa Application Protocol Data Unit, que é um tipo de mensagem usada em terminais de pagamento ou terminais de caixa eletrônico para comunicar com terminais de rede. Ela é usada para transferir dados entre dispositivos de hardware e software. A APDU é comumente usada em sistemas de pagamento sem contato, como cartões de crédito e débito. Ela é composta por uma sequência de comandos e dados que são enviados e recebidos entre os dispositivos.

Métricas reportadas pelo Ollama: 74 tokens de entrada, 117 tokens de saída,
5,31 segundos (tempo do servidor, não medição ponta a ponta).

Análise: a chamada HTTP e a geração funcionaram. O texto é fluente, mas
“comunicar com terminais de rede” é uma descrição imprecisa e a explicação
é genérica. Não usar essa resposta como documentação técnica validada.
A precisão deverá ser comparada com documentação de referência durante as fases de RAG.

Próximo passo: executar os experimentos do README e registrar as diferenças.
Não avançar para a Fase 2 antes de analisar esses resultados com o usuário.
