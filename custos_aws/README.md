# Painel de custos AWS

Streamlit sobre os dados de custo que a Nekt já coleta da AWS. Não fala com a AWS: lê o
lake, então enxerga exatamente o que a plataforma enxerga.

```bash
cd ~/Projetos/data_visualization/custos_aws
source ~/.config/locates/secrets.env      # exporta NEKT_MCP_TOKEN
.venv/bin/streamlit run app.py
```

Primeira vez:

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## De onde vêm os dados

Source `aws-cost-explorer-jfdJ` (conector AWS Cost Explorer), camada Raw, três streams
incrementais de granularidade diária e métrica `UnblendedCost` em USD:

| tabela | grão |
|---|---|
| `nekt_raw.aws_cost_explorer_cost_and_usage` | total da conta por dia |
| `nekt_raw.aws_cost_explorer_cost_by_service` | custo por serviço por dia |
| `nekt_raw.aws_cost_explorer_cost_by_linked_account` | custo por conta vinculada por dia |

A chave `(time_period_start, group_by_value, metric_name)` garante que sincronizações
repetidas não dupliquem linhas — os totais das três tabelas batem centavo a centavo.

## Por que via MCP e não pela API REST

A API v1 da Nekt (`https://api.nekt.ai`) lista tabelas, sources e transformações, mas
**não executa SQL**: `/api/v1/queries/` só guarda o texto da query. Quem roda no Athena é
a ferramenta `execute_sql` do MCP server (`https://mcp.locates.com.br/mcp`), autenticada
com `NEKT_MCP_TOKEN`. `nekt_client.py` é um cliente HTTP fino desse protocolo — handshake
`initialize`, `tools/call`, resposta em JSON ou SSE.

O volume é pequeno (< 4k linhas somadas), então os três streams são carregados inteiros
uma vez, com cache de 30 minutos, e todo filtro do painel acontece em pandas.

## Armadilhas dos dados, já tratadas no código

- **O histórico útil começa em abril/2026.** Os meses anteriores existem nas tabelas com
  custo zero — resíduos da ordem de 1e-9, não zero limpo, o que faria um teste `> 0`
  disparar no primeiro dia da série. Daí o limiar de 1 USD/dia em
  `dados.primeiro_dia_com_custo`.
- **O último dia é sempre parcial.** O sync roda por volta do meio-dia e captura o dia em
  curso pela metade. Ele aparece marcado nos gráficos e nunca entra em média, projeção ou
  comparação (`dados.ultimo_dia_fechado`).
- **O pico do dia 1º de cada mês é imposto**, não pico de uso: a linha `Tax` do Cost
  Explorer lança o mês inteiro de uma vez (US$ 190,66 em 01/jul; US$ 151,80 em 01/ago).
  O gráfico diário anota isso. É também por isso que o indicador do topo é a *soma* dos
  últimos 30 dias e não uma média extrapolada — multiplicar uma média que não contém um
  dia 1º subestima o mês.
- **Valores negativos são créditos e estornos**, recorrentes em `AWS Data Transfer`.
- **Só a conta 860134658538 tem custo**; a vinculada 194722401664 está zerada.
- Comparação de composição usa apenas meses completos; o mês em curso viraria uma coluna
  raquítica e sugeriria uma queda inexistente.

## Arquivos

| arquivo | papel |
|---|---|
| `app.py` | layout, filtros e narrativa do painel |
| `dados.py` | SQL de carga, janelas de validade e agregações |
| `graficos.py` | figuras Plotly |
| `tema.py` | superfícies, paleta categórica e CSS |
| `formatos.py` | moeda pt-BR, meses e nomes curtos dos serviços AWS |

A paleta de séries é a de referência da skill de dataviz, validada contra a superfície
`#16161c` (banda de luminosidade, piso de croma, separação para daltonismo, piso de visão
normal e contraste ≥ 3:1). As cores da marca Locates ficam na moldura, não nas séries.
Cor é fixada por serviço a partir do ranking do histórico inteiro, então mudar o filtro
não repinta as séries.
