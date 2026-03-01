# Índice Locates (Streamlit)

Dashboard Streamlit para análise de indicadores de empreendimentos imobiliários com visual inspirado na identidade da Locates.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para rodar a versão com consulta SQL completa:

```bash
streamlit run sonnet_app.py
```

## Variáveis de ambiente (PostgreSQL)

Defina no ambiente antes de iniciar o app:

- `DB_NAME`
- `HOST_URL`
- `DB_PASS`
- `DB_USER`
- `SCHEMA`
- `DB_PORT` (opcional, padrão `5432`)

## Base de dados esperada (CSV)

Colunas obrigatórias:

- `data_referencia`
- `cidade`
- `categoria`
- `empreendimento`
- `vgv`
- `custo`
- `unidades`
- `area_m2`

Sem upload de arquivo, o app usa uma base de demonstração automaticamente.
