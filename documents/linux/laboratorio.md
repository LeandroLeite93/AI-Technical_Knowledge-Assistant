# Laboratório de logs

Este é um documento fictício para testar ingestão, não uma referência de produção.

## Cenário de teste

O terminal 1002 registrou um timeout ao tentar conectar ao serviço de autorização.
Neste laboratório, o arquivo de log de exemplo se chama transaction.log.
Antes de propor uma alteração, compare o horário da falha com o estado do serviço.

## Configuração de exemplo

O trecho abaixo é apenas um exemplo didático. Nenhum arquivo é executado pelo pipeline.

```ini
terminal_id=1002
timeout_seconds=30
```

## Como usar este documento

O pipeline deve preservar o nome linux/laboratorio.md como origem e LINUX como categoria.
Por ser Markdown, o número de página é nulo. O texto é dividido em janelas de caracteres.
