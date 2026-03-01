import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Índice LOCATES",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Tokens ── */
:root {
    --bg:         #0D0F1A;
    --surface:    #13162A;
    --surface-2:  #1A1E35;
    --border:     rgba(255,255,255,0.07);
    --green:      #00E5A0;
    --green-dim:  rgba(0,229,160,0.12);
    --green-glow: rgba(0,229,160,0.25);
    --purple:     #6C5CE7;
    --purple-dim: rgba(108,92,231,0.15);
    --text:       #E8EAFF;
    --muted:      #6B7194;
    --muted-2:    #9198BE;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
    font-family: 'Outfit', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header, [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--purple); border-radius: 10px; }

/* ──────────────────────────────────────────────
   HEADER
────────────────────────────────────────────── */
.loc-header {
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 48px;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
}
.loc-logo {
    font-family: 'Outfit', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text);
}
.loc-logo span { color: var(--green); }
.header-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--green-dim);
    border: 1px solid rgba(0,229,160,0.3);
    color: var(--green);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 20px;
}
.header-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.85); }
}

/* ──────────────────────────────────────────────
   HERO
────────────────────────────────────────────── */
.loc-hero {
    background: linear-gradient(160deg, #0D0F1A 0%, #121528 60%, #0E1020 100%);
    padding: 72px 48px 56px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.loc-hero::before {
    content: '';
    position: absolute;
    top: -120px; left: 50%;
    transform: translateX(-50%);
    width: 700px; height: 400px;
    background: radial-gradient(ellipse, rgba(108,92,231,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.loc-hero::after {
    content: '';
    position: absolute;
    bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,229,160,0.4), transparent);
}
.hero-eyebrow {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--green);
    margin-bottom: 16px;
}
.hero-h1 {
    font-size: 3.4rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
    line-height: 1;
    margin-bottom: 16px;
}
.hero-h1 em {
    font-style: normal;
    background: linear-gradient(90deg, #00E5A0, #6C5CE7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.95rem;
    color: var(--muted-2);
    font-weight: 400;
    line-height: 1.6;
    max-width: 480px;
    margin: 0 auto;
}

/* ──────────────────────────────────────────────
   TABS
────────────────────────────────────────────── */
div[data-testid="stTabs"] > div:first-child {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    justify-content: center !important;
    gap: 0 !important;
    padding: 0 48px !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    padding: 18px 32px !important;
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    transition: color 0.2s !important;
}
div[data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--text) !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--green) !important;
    border-bottom: 2px solid var(--green) !important;
}
div[data-testid="stTabs"] [data-testid="stTabContent"] {
    padding: 0 !important;
    background: var(--bg) !important;
}

/* ──────────────────────────────────────────────
   CONTENT
────────────────────────────────────────────── */
.content {
    max-width: 1160px;
    margin: 0 auto;
    padding: 40px 32px 80px;
}

/* ── KPI Grid ── */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 36px;
}
.kpi {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi:hover { border-color: rgba(0,229,160,0.25); }
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--green), transparent);
}
.kpi-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
}
.kpi-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
    line-height: 1;
}
.kpi-delta {
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--green);
    margin-top: 7px;
}

/* ── Section labels ── */
.sec-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}
.sec-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 24px;
}

/* ── Filter bar ── */
.filter-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 28px;
}

/* ── Table header card ── */
.tbl-head {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.tbl-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text);
    flex: 1;
}
.tbl-pill {
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--green);
    background: var(--green-dim);
    border: 1px solid rgba(0,229,160,0.2);
    padding: 4px 10px;
    border-radius: 20px;
}
.tbl-icon { font-size: 0.85rem; opacity: 0.7; }

/* ── Streamlit table/dataframe ── */
[data-testid="stDataFrame"] > div {
    border-radius: 0 0 10px 10px !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    overflow: hidden !important;
    background: var(--surface) !important;
}

/* ── Selectbox ── */
.stSelectbox label {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

/* ── Multiselect ── */
.stMultiSelect label {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stMultiSelect"] > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Footer ── */
.loc-footer {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 44px 80px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 48px;
}
.loc-footer h5 {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--green);
    margin-bottom: 10px;
}
.loc-footer p {
    font-size: 0.8rem;
    color: var(--muted-2);
    line-height: 1.65;
}
.loc-copy {
    background: var(--bg);
    text-align: center;
    padding: 16px;
    font-size: 0.68rem;
    color: var(--muted);
    letter-spacing: 0.08em;
    border-top: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ─── DATA ─────────────────────────────────────────────────────────────────────
CITY_DATA = {
    "Balneário Camboriú": {"preco": 27807.50, "3m": 5.69, "6m": 12.70, "12m": 19.40},
    "Itapema":            {"preco": 20997.50, "3m": 5.27, "6m": 10.98, "12m": 16.68},
    "Bombinhas":          {"preco": 18387.00, "3m": 2.57, "6m":  7.19, "12m": 11.70},
    "Porto Belo":         {"preco": 17252.00, "3m": 4.03, "6m":  8.95, "12m": 13.45},
    "Garopaba":           {"preco": 16457.50, "3m": 2.64, "6m":  6.25, "12m": 10.44},
    "Itajaí":             {"preco": 15663.00, "3m": 4.98, "6m": 10.53, "12m": 15.77},
    "Gov. Celso Ramos":   {"preco": 15663.00, "3m": 3.35, "6m":  7.80, "12m": 12.22},
    "Piçarras":           {"preco": 13393.00, "3m": 3.88, "6m":  9.17, "12m": 14.49},
    "Florianópolis":      {"preco": 13157.01, "3m": 4.11, "6m":  5.65, "12m": 10.41},
    "Penha":              {"preco": 12712.00, "3m": 3.33, "6m":  8.85, "12m": 14.06},
    "Joinville":          {"preco": 12258.00, "3m": 3.06, "6m":  6.38, "12m":  9.94},
    "Navegantes":         {"preco": 11917.50, "3m": 4.61, "6m":  8.64, "12m": 12.74},
    "Imbituba":           {"preco": 11123.00, "3m": 2.06, "6m":  5.80, "12m":  9.15},
    "Barra Velha":        {"preco": 10442.00, "3m": 3.12, "6m":  6.78, "12m": 10.25},
    "Laguna":             {"preco": 10101.50, "3m": 1.97, "6m":  4.99, "12m":  8.56},
    "Palhoça":            {"preco":  9870.00, "3m": 3.45, "6m":  7.10, "12m": 11.30},
    "São José":           {"preco":  9540.00, "3m": 2.85, "6m":  6.20, "12m": 10.05},
}

MONTHS = ["Mar/23","Abr/23","Mai/23","Jun/23","Jul/23","Ago/23",
          "Set/23","Out/23","Nov/23","Dez/23","Jan/24","Fev/24"]

HISTORY = {
    "Balneário Camboriú": [23301,23606,24095,24357,24789,25170,25609,25920,26345,26716,27019,27808],
    "Itapema":            [17995,18229,18512,18790,18973,19262,19532,19793,19960,20238,20491,20998],
    "Bombinhas":          [16422,16615,16791,16951,17077,17283,17436,17543,17765,17934,18092,18397],
    "Porto Belo":         [14890,15102,15344,15580,15710,15940,16070,16210,16430,16680,16900,17252],
    "Garopaba":           [14870,15010,15150,15280,15370,15510,15640,15760,15910,16050,16230,16457],
    "Itajaí":             [13510,13620,13750,13880,14050,14210,14380,14520,14720,14900,15100,15663],
    "Florianópolis":      [11890,11950,12020,12100,12200,12310,12430,12540,12680,12790,12960,13157],
}

BAIRROS = {
    "Barra Sul":         {"preco": 35200.00, "3m": 7.20, "6m": 14.80, "12m": 24.10},
    "Centro":            {"preco": 31500.00, "3m": 6.10, "6m": 13.20, "12m": 21.50},
    "Barra Norte":       {"preco": 28900.00, "3m": 5.50, "6m": 11.90, "12m": 18.70},
    "Pioneiros":         {"preco": 26100.00, "3m": 4.80, "6m": 10.20, "12m": 16.30},
    "Nações":            {"preco": 24300.00, "3m": 4.20, "6m":  9.10, "12m": 14.90},
    "Agronomica":        {"preco": 22800.00, "3m": 3.90, "6m":  8.30, "12m": 13.50},
    "Tabuleiro":         {"preco": 19500.00, "3m": 3.20, "6m":  7.00, "12m": 11.20},
}

PALETTE = ["#00E5A0", "#6C5CE7", "#00B4D8", "#F5A623", "#FF6B9D", "#A8DADC", "#E9C46A"]

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(v):
    return f"+{v:.2f}%"


def _db_env_config() -> dict:
    return {
        "dbname": os.getenv("DB_NAME"),
        "host": os.getenv("HOST_URL"),
        "password": os.getenv("DB_PASS"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER"),
        "schema": os.getenv("SCHEMA", "public"),
    }


def _parse_jsonb(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_market_payload(lat: float, lon: float, raio: int, data_ref_sql: str | None):
    cfg = _db_env_config()
    required = ["dbname", "host", "password", "user", "schema"]
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        raise ValueError(
            "Variáveis de ambiente ausentes: " + ", ".join(missing)
        )

    query = sql.SQL(
        """
WITH params AS (
    SELECT
        %(lat)s::double precision AS lat,
        %(lon)s::double precision AS lon,
        %(raio)s::double precision AS raio,
        NULLIF(%(data_ref_sql)s, '')::date AS data_ref_sql
),
tipologias AS (
    SELECT *
    FROM (VALUES
        ('flat'),
        ('cobertura'),
        ('galpao_deposito_armazem'),
        ('consultorio'),
        ('fazenda_sitios_chacaras'),
        ('escritorio'),
        ('sobrado'),
        ('lote_terreno'),
        ('predio_edificio_inteiro'),
        ('apartamento'),
        ('casa_de_condominio'),
        ('imovel_comercial'),
        ('edificio_residencial'),
        ('ponto_comercial_loja_box'),
        ('casa')
    ) t(tipo_imovel)
),
datas_disponiveis AS (
    SELECT DISTINCT
        bl_lancamento,
        data_tabela,
        DATE_TRUNC('month', data_tabela) AS mes_referencia
    FROM {schema}.api_mercado
),
meses_alvo AS (
    SELECT
        b.bl_lancamento,
        DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(b.data_tabela))) AS mes_atual,
        DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(b.data_tabela))) - INTERVAL '2 months'  AS mes_menos_2,
        DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(b.data_tabela))) - INTERVAL '5 months'  AS mes_menos_5,
        DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(b.data_tabela))) - INTERVAL '8 months'  AS mes_menos_8,
        DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(b.data_tabela))) - INTERVAL '11 months' AS mes_menos_11
    FROM {schema}.api_mercado b
    GROUP BY b.bl_lancamento
),
liquidez_anuncios AS (
    SELECT
        b.id_fonte,
        b.bl_lancamento,
        b.tipo_negocio,
        LOWER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(unaccent(b.tipo_imovel), '[^a-zA-Z0-9]+', '_', 'g'),
                '^_|_$', ''
            )
        ) AS tipo_imovel,
        EXTRACT(EPOCH FROM (MAX(b.data_tabela) - MIN(b.data_tabela))) / 86400 AS dias_no_mercado
    FROM {schema}.api_mercado b
    INNER JOIN meses_alvo m
        ON  b.bl_lancamento = m.bl_lancamento
        AND b.data_tabela BETWEEN m.mes_menos_11
                              AND m.mes_atual + INTERVAL '1 month' - INTERVAL '1 day'
    CROSS JOIN params p
    WHERE ST_DWithin(
        b.geom_anuncio,
        ST_Transform(ST_SetSRID(ST_MakePoint(p.lon, p.lat), 4326), 31982),
        p.raio
    )
    GROUP BY b.id_fonte, b.bl_lancamento, b.tipo_negocio, b.tipo_imovel
),
agg_liquidez AS (
    SELECT
        CASE WHEN bl_lancamento THEN 'lancamentos' ELSE 'mercado' END AS origem,
        tipo_negocio,
        tipo_imovel,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_no_mercado) AS liquidez_dias
    FROM liquidez_anuncios
    GROUP BY CASE WHEN bl_lancamento THEN 'lancamentos' ELSE 'mercado' END, tipo_negocio, tipo_imovel
),
datas_selecionadas AS (
    SELECT DISTINCT ON (m.bl_lancamento, periodo)
        m.bl_lancamento,
        d.data_tabela,
        periodo
    FROM meses_alvo m
    CROSS JOIN LATERAL (
        VALUES
            ('atual',    m.mes_atual),
            ('menos_2',  m.mes_menos_2),
            ('menos_5',  m.mes_menos_5),
            ('menos_8',  m.mes_menos_8),
            ('menos_11', m.mes_menos_11)
    ) AS p(periodo, mes_alvo)
    INNER JOIN datas_disponiveis d
        ON  d.bl_lancamento  = m.bl_lancamento
        AND d.mes_referencia BETWEEN mes_alvo - INTERVAL '1 month'
                                 AND mes_alvo
    ORDER BY
        m.bl_lancamento,
        periodo,
        ABS(EXTRACT(EPOCH FROM (d.mes_referencia - mes_alvo))),
        d.data_tabela DESC
),
base AS (
    SELECT
        CASE WHEN b.bl_lancamento THEN 'lancamentos' ELSE 'mercado' END AS origem,
        d.periodo,
        b.tipo_negocio,
        LOWER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(unaccent(b.tipo_imovel), '[^a-zA-Z0-9]+', '_', 'g'),
                '^_|_$', ''
            )
        ) AS tipo_imovel,
        b.num_quartos,
        b.faixa_area,
        b.area,
        b.valor / NULLIF(b.area, 0) AS valor_m2
    FROM {schema}.api_mercado b
    INNER JOIN datas_selecionadas d
        ON  b.data_tabela   = d.data_tabela
        AND b.bl_lancamento = d.bl_lancamento
    CROSS JOIN params p
    WHERE ST_DWithin(
        b.geom_anuncio,
        ST_Transform(ST_SetSRID(ST_MakePoint(p.lon, p.lat), 4326), 31982),
        p.raio
    )
),
agg AS (
    SELECT
        origem,
        tipo_negocio,
        tipo_imovel,
        periodo,
        COUNT(*) AS qtd_anuncios,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) AS media_geral,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE num_quartos = '1')  AS d1,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE num_quartos = '2')  AS d2,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE num_quartos = '3')  AS d3,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE num_quartos = '4')  AS d4,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE num_quartos = '5+') AS d5,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '46 a 60m²')   AS a_46_60,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '61 a 75m²')   AS a_61_75,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '76 a 90m²')   AS a_76_90,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '91 a 115m²')  AS a_91_115,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '116 a 145m²') AS a_116_145,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '146 a 175m²') AS a_146_175,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '176 a 200m²') AS a_176_200,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area = '201 a 300m²') AS a_201_300,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE faixa_area ILIKE 'Maior%%')  AS a_maior_300,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 0     AND 1000)  AS g_0_1000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 1001  AND 2000)  AS g_1001_2000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 2001  AND 3000)  AS g_2001_3000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 3001  AND 4000)  AS g_3001_4000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 4001  AND 5000)  AS g_4001_5000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 5001  AND 7500)  AS g_5001_7500,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 7501  AND 10000) AS g_7501_10000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 10001 AND 15000) AS g_10001_15000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area BETWEEN 15001 AND 20000) AS g_15001_20000,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE area > 20000)                 AS g_maior_20000
    FROM base
    GROUP BY origem, tipo_negocio, tipo_imovel, periodo
),
agg_com_variacao AS (
    SELECT
        a.origem,
        a.tipo_negocio,
        a.tipo_imovel,
        MAX(a.qtd_anuncios) FILTER (WHERE a.periodo = 'atual') AS qtd_anuncios,
        MAX(a.media_geral)  FILTER (WHERE a.periodo = 'atual') AS media_geral,
        l.liquidez_dias,
        CASE
            WHEN MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_2') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_2') > 0
            THEN ROUND(((MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') - MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_2')) / MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_2'))::numeric * 100, 2)
        END AS variacao_3m,
        CASE
            WHEN MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_5') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_5') > 0
            THEN ROUND(((MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') - MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_5')) / MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_5'))::numeric * 100, 2)
        END AS variacao_6m,
        CASE
            WHEN MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_8') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_8') > 0
            THEN ROUND(((MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') - MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_8')) / MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_8'))::numeric * 100, 2)
        END AS variacao_9m,
        CASE
            WHEN MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_11') IS NOT NULL
             AND MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_11') > 0
            THEN ROUND(((MAX(a.media_geral) FILTER (WHERE a.periodo = 'atual') - MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_11')) / MAX(a.media_geral) FILTER (WHERE a.periodo = 'menos_11'))::numeric * 100, 2)
        END AS variacao_12m,
        MAX(a.d1) FILTER (WHERE a.periodo = 'atual') AS d1,
        MAX(a.d2) FILTER (WHERE a.periodo = 'atual') AS d2,
        MAX(a.d3) FILTER (WHERE a.periodo = 'atual') AS d3,
        MAX(a.d4) FILTER (WHERE a.periodo = 'atual') AS d4,
        MAX(a.d5) FILTER (WHERE a.periodo = 'atual') AS d5,
        MAX(a.a_46_60) FILTER (WHERE a.periodo = 'atual') AS a_46_60,
        MAX(a.a_61_75) FILTER (WHERE a.periodo = 'atual') AS a_61_75,
        MAX(a.a_76_90) FILTER (WHERE a.periodo = 'atual') AS a_76_90,
        MAX(a.a_91_115) FILTER (WHERE a.periodo = 'atual') AS a_91_115,
        MAX(a.a_116_145) FILTER (WHERE a.periodo = 'atual') AS a_116_145,
        MAX(a.a_146_175) FILTER (WHERE a.periodo = 'atual') AS a_146_175,
        MAX(a.a_176_200) FILTER (WHERE a.periodo = 'atual') AS a_176_200,
        MAX(a.a_201_300) FILTER (WHERE a.periodo = 'atual') AS a_201_300,
        MAX(a.a_maior_300) FILTER (WHERE a.periodo = 'atual') AS a_maior_300,
        MAX(a.g_0_1000) FILTER (WHERE a.periodo = 'atual') AS g_0_1000,
        MAX(a.g_1001_2000) FILTER (WHERE a.periodo = 'atual') AS g_1001_2000,
        MAX(a.g_2001_3000) FILTER (WHERE a.periodo = 'atual') AS g_2001_3000,
        MAX(a.g_3001_4000) FILTER (WHERE a.periodo = 'atual') AS g_3001_4000,
        MAX(a.g_4001_5000) FILTER (WHERE a.periodo = 'atual') AS g_4001_5000,
        MAX(a.g_5001_7500) FILTER (WHERE a.periodo = 'atual') AS g_5001_7500,
        MAX(a.g_7501_10000) FILTER (WHERE a.periodo = 'atual') AS g_7501_10000,
        MAX(a.g_10001_15000) FILTER (WHERE a.periodo = 'atual') AS g_10001_15000,
        MAX(a.g_15001_20000) FILTER (WHERE a.periodo = 'atual') AS g_15001_20000,
        MAX(a.g_maior_20000) FILTER (WHERE a.periodo = 'atual') AS g_maior_20000
    FROM agg a
    LEFT JOIN agg_liquidez l
        ON  l.origem       = a.origem
        AND l.tipo_negocio = a.tipo_negocio
        AND l.tipo_imovel  = a.tipo_imovel
    GROUP BY a.origem, a.tipo_negocio, a.tipo_imovel, l.liquidez_dias
),
origens AS (
    SELECT 'mercado' AS origem
    UNION ALL
    SELECT 'lancamentos' AS origem
),
negocios AS (
    SELECT 'Venda' AS tipo_negocio
    UNION ALL
    SELECT 'Aluguel' AS tipo_negocio
),
grid AS (
    SELECT o.origem, n.tipo_negocio, t.tipo_imovel
    FROM origens o
    CROSS JOIN negocios n
    CROSS JOIN tipologias t
),
json_por_origem AS (
    SELECT
        g.origem,
        g.tipo_negocio,
        jsonb_object_agg(
            g.tipo_imovel,
            jsonb_build_object(
                'media_geral',   ROUND(a.media_geral::numeric, 2),
                'liquidez_dias', ROUND(a.liquidez_dias::numeric, 0),
                'variacao_3m',   ROUND(a.variacao_3m, 2),
                'variacao_6m',   ROUND(a.variacao_6m, 2),
                'variacao_9m',   ROUND(a.variacao_9m, 2),
                'variacao_12m',  ROUND(a.variacao_12m, 2),
                'qtd_anuncios',  a.qtd_anuncios,
                'disponivel',    COALESCE(a.qtd_anuncios, 0) >= 10
            )
            ||
            CASE
                WHEN g.tipo_imovel IN ('lote_terreno', 'fazenda_sitios_chacaras') THEN
                    jsonb_build_object(
                        '0_a_1000m2',      ROUND(a.g_0_1000::numeric, 2),
                        '1001_a_2000m2',   ROUND(a.g_1001_2000::numeric, 2),
                        '2001_a_3000m2',   ROUND(a.g_2001_3000::numeric, 2),
                        '3001_a_4000m2',   ROUND(a.g_3001_4000::numeric, 2),
                        '4001_a_5000m2',   ROUND(a.g_4001_5000::numeric, 2),
                        '5001_a_7500m2',   ROUND(a.g_5001_7500::numeric, 2),
                        '7501_a_10000m2',  ROUND(a.g_7501_10000::numeric, 2),
                        '10001_a_15000m2', ROUND(a.g_10001_15000::numeric, 2),
                        '15001_a_20000m2', ROUND(a.g_15001_20000::numeric, 2),
                        'maior_20000m2',   ROUND(a.g_maior_20000::numeric, 2)
                    )
                ELSE
                    jsonb_build_object(
                        '1d',          ROUND(a.d1::numeric, 2),
                        '2d',          ROUND(a.d2::numeric, 2),
                        '3d',          ROUND(a.d3::numeric, 2),
                        '4d',          ROUND(a.d4::numeric, 2),
                        '5d+',         ROUND(a.d5::numeric, 2),
                        '46_a_60m2',   ROUND(a.a_46_60::numeric, 2),
                        '61_a_75m2',   ROUND(a.a_61_75::numeric, 2),
                        '76_a_90m2',   ROUND(a.a_76_90::numeric, 2),
                        '91_a_115m2',  ROUND(a.a_91_115::numeric, 2),
                        '116_a_145m2', ROUND(a.a_116_145::numeric, 2),
                        '146_a_175m2', ROUND(a.a_146_175::numeric, 2),
                        '176_a_200m2', ROUND(a.a_176_200::numeric, 2),
                        '201_a_300m2', ROUND(a.a_201_300::numeric, 2),
                        'maior_300m2', ROUND(a.a_maior_300::numeric, 2)
                    )
            END
        ) AS payload
    FROM grid g
    LEFT JOIN agg_com_variacao a
        ON  a.origem       = g.origem
        AND a.tipo_negocio = g.tipo_negocio
        AND a.tipo_imovel  = g.tipo_imovel
    GROUP BY g.origem, g.tipo_negocio
)
SELECT jsonb_build_object(
    'venda',
        (SELECT payload FROM json_por_origem WHERE origem = 'mercado'     AND tipo_negocio = 'Venda'),
    'aluguel',
        (SELECT payload FROM json_por_origem WHERE origem = 'mercado'     AND tipo_negocio = 'Aluguel'),
    'lancamentos', jsonb_build_object(
        'venda',
            (SELECT payload FROM json_por_origem WHERE origem = 'lancamentos' AND tipo_negocio = 'Venda'),
        'aluguel',
            (SELECT payload FROM json_por_origem WHERE origem = 'lancamentos' AND tipo_negocio = 'Aluguel')
    )
) AS data;
        """
    ).format(schema=sql.Identifier(cfg["schema"]))

    params = {
        "lat": lat,
        "lon": lon,
        "raio": raio,
        "data_ref_sql": data_ref_sql,
    }

    with psycopg.connect(
        dbname=cfg["dbname"],
        host=cfg["host"],
        password=cfg["password"],
        port=cfg["port"],
        user=cfg["user"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if not row:
                return {}
            return _parse_jsonb(row[0])


def payload_to_dataframe(payload: dict, origem: str, negocio: str) -> pd.DataFrame:
    if not payload:
        return pd.DataFrame()

    if origem == "mercado":
        data = payload.get(negocio, {})
    else:
        data = payload.get("lancamentos", {}).get(negocio, {})

    rows = []
    for tipo, metrics in (data or {}).items():
        rows.append(
            {
                "tipologia": tipo,
                "media_geral": metrics.get("media_geral"),
                "qtd_anuncios": metrics.get("qtd_anuncios"),
                "liquidez_dias": metrics.get("liquidez_dias"),
                "variacao_3m": metrics.get("variacao_3m"),
                "variacao_6m": metrics.get("variacao_6m"),
                "variacao_12m": metrics.get("variacao_12m"),
                "disponivel": metrics.get("disponivel"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("media_geral", ascending=False, na_position="last")
    return df


def _pick_name_column(conn, table_schema: str, table_name: str, candidates: list[str]) -> str | None:
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (table_schema, table_name))
        existing = {row[0] for row in cur.fetchall()}

    for column in candidates:
        if column in existing:
            return column
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_geo_rankings(
    lat: float,
    lon: float,
    raio: int,
    data_ref_sql: str | None,
    tipo_negocio: str | None,
    tipo_imovel_norm: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = _db_env_config()
    required = ["dbname", "host", "password", "user", "schema"]
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        raise ValueError("Variáveis de ambiente ausentes: " + ", ".join(missing))

    with psycopg.connect(
        dbname=cfg["dbname"],
        host=cfg["host"],
        password=cfg["password"],
        port=cfg["port"],
        user=cfg["user"],
    ) as conn:
        query = sql.SQL(
            """
WITH params AS (
    SELECT
        %(lat)s::double precision AS lat,
        %(lon)s::double precision AS lon,
        %(raio)s::double precision AS raio,
        NULLIF(%(data_ref_sql)s, '')::date AS data_ref_sql,
        NULLIF(%(tipo_negocio)s, '')::text AS tipo_negocio,
        NULLIF(%(tipo_imovel_norm)s, '')::text AS tipo_imovel_norm
),
mes_ref AS (
    SELECT DATE_TRUNC('month', COALESCE((SELECT data_ref_sql FROM params), MAX(data_tabela))) AS mes
    FROM {api_schema}.api_mercado
),
anuncios_filtrados AS (
    SELECT
        b.id_fonte,
        b.geom_anuncio,
        b.tipo_negocio,
        LOWER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(unaccent(b.tipo_imovel), '[^a-zA-Z0-9]+', '_', 'g'),
                '^_|_$', ''
            )
        ) AS tipo_imovel_norm,
        b.valor / NULLIF(b.area, 0) AS valor_m2
    FROM {api_schema}.api_mercado b
    CROSS JOIN params p
    CROSS JOIN mes_ref m
    WHERE DATE_TRUNC('month', b.data_tabela) = m.mes
      AND ST_DWithin(
            b.geom_anuncio,
            ST_Transform(ST_SetSRID(ST_MakePoint(p.lon, p.lat), 4326), ST_SRID(b.geom_anuncio)),
            p.raio
      )
      AND (p.tipo_negocio IS NULL OR b.tipo_negocio = p.tipo_negocio)
      AND (p.tipo_imovel_norm IS NULL OR LOWER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(unaccent(b.tipo_imovel), '[^a-zA-Z0-9]+', '_', 'g'),
                '^_|_$', ''
            )
      ) = p.tipo_imovel_norm)
),
anuncios_geocodificados AS (
    SELECT
        a.id_fonte,
        gm.nm_mun AS municipio,
        gb.nm_bairro AS bairro,
        a.tipo_negocio,
        a.tipo_imovel_norm,
        a.valor_m2
    FROM anuncios_filtrados a
    LEFT JOIN LATERAL (
        SELECT m.nm_mun, m.geom
        FROM geo_floripa.cad_mun m
        WHERE ST_Covers(m.geom, ST_Transform(a.geom_anuncio, ST_SRID(m.geom)))
        ORDER BY m.cd_mun
        LIMIT 1
    ) gm ON TRUE
    LEFT JOIN LATERAL (
        SELECT b.nm_bairro
        FROM geo_floripa.cad_bairro b
        WHERE ST_Covers(b.geom, ST_Transform(a.geom_anuncio, ST_SRID(b.geom)))
        ORDER BY b.cd_bairro
        LIMIT 1
    ) gb ON TRUE
),
cidades AS (
    SELECT
        municipio AS local,
        COUNT(*) AS qtd_anuncios,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) AS mediana_m2,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE tipo_negocio = 'Venda') AS mediana_venda,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) FILTER (WHERE tipo_negocio = 'Aluguel') AS mediana_aluguel
    FROM anuncios_geocodificados
    WHERE municipio IS NOT NULL
    GROUP BY municipio
),
bairros AS (
    SELECT
        municipio,
        bairro AS local,
        COUNT(*) AS qtd_anuncios,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_m2) AS mediana_m2
    FROM anuncios_geocodificados
    WHERE bairro IS NOT NULL
    GROUP BY municipio, bairro
)
SELECT
    'cidade'::text AS nivel,
    local,
    NULL::text AS municipio,
    qtd_anuncios,
    mediana_m2,
    mediana_venda,
    mediana_aluguel
FROM cidades
UNION ALL
SELECT
    'bairro'::text AS nivel,
    local,
    municipio,
    qtd_anuncios,
    mediana_m2,
    NULL::double precision AS mediana_venda,
    NULL::double precision AS mediana_aluguel
FROM bairros;
            """
        ).format(
            api_schema=sql.Identifier(cfg["schema"]),
        )

        params = {
            "lat": lat,
            "lon": lon,
            "raio": raio,
            "data_ref_sql": data_ref_sql,
            "tipo_negocio": tipo_negocio,
            "tipo_imovel_norm": tipo_imovel_norm,
        }

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_cidades = df[df["nivel"] == "cidade"].copy()
    df_bairros = df[df["nivel"] == "bairro"].copy()

    if not df_cidades.empty:
        df_cidades = df_cidades.sort_values("mediana_m2", ascending=False)
    if not df_bairros.empty:
        df_bairros = df_bairros.sort_values(["municipio", "mediana_m2"], ascending=[True, False])

    return df_cidades, df_bairros

# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────
PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit, sans-serif", color="#9198BE"),
)

def dark_axes(fig, xgrid=False, ygrid=True):
    fig.update_xaxes(
        showgrid=xgrid, gridcolor="rgba(255,255,255,0.05)",
        zeroline=False, tickfont=dict(size=11, color="#6B7194"),
        linecolor="rgba(255,255,255,0.07)",
    )
    fig.update_yaxes(
        showgrid=ygrid, gridcolor="rgba(255,255,255,0.05)",
        zeroline=False, tickfont=dict(size=11, color="#6B7194"),
        linecolor="rgba(255,255,255,0.07)",
    )
    return fig

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="loc-header">
    <div class="loc-logo">LOCATES<span>.</span></div>
    <div class="header-badge">
        <div class="header-dot"></div>
        Índice · Fevereiro 2024
    </div>
</div>
""", unsafe_allow_html=True)

# ─── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="loc-hero">
    <div class="hero-eyebrow">Inteligência Imobiliária · Santa Catarina</div>
    <div class="hero-h1">Índice <em>LOCATES</em></div>
    <div class="hero-sub">
        Monitoramento estratégico e comparativo de dados de mercado imobiliário
        em tempo real para incorporadores, investidores e urbanistas.
    </div>
</div>
""", unsafe_allow_html=True)

# ─── SQL INPUTS / LOAD ───────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Conexão PostgreSQL")
    st.caption("Variáveis esperadas: DB_NAME, HOST_URL, DB_PASS, DB_USER, SCHEMA")
    sql_lat = st.number_input("Latitude", value=-27.5954, format="%.6f")
    sql_lon = st.number_input("Longitude", value=-48.5480, format="%.6f")
    sql_raio = st.number_input("Raio (m)", min_value=100, max_value=100000, value=1000, step=100)
    sql_data_ref = st.text_input("Data referência (YYYY-MM-DD)", value="")
    sql_refresh = st.button("Atualizar dados SQL", type="primary", use_container_width=True)

if "sql_payload" not in st.session_state:
    st.session_state["sql_payload"] = None
    st.session_state["sql_error"] = None

if sql_refresh or st.session_state["sql_payload"] is None:
    try:
        st.session_state["sql_payload"] = fetch_market_payload(
            lat=float(sql_lat),
            lon=float(sql_lon),
            raio=int(sql_raio),
            data_ref_sql=sql_data_ref.strip() or None,
        )
        st.session_state["sql_error"] = None
    except Exception as exc:
        st.session_state["sql_error"] = str(exc)
        if st.session_state["sql_payload"] is None:
            st.session_state["sql_payload"] = {}

if st.session_state.get("sql_error"):
    st.warning(f"SQL indisponível: {st.session_state['sql_error']}")
elif st.session_state.get("sql_payload"):
    st.success("Dados SQL carregados com sucesso.")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_cidade, tab_bairros = st.tabs(["  Índice Locates Cidade  ", "  Índice Locates Bairros  "])

# ═══════════════════════════════════════════════════════════
#  TAB CIDADE
# ═══════════════════════════════════════════════════════════
with tab_cidade:
    st.markdown('<div class="content">', unsafe_allow_html=True)

    # ── Filters SQL ──
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        sql_origem = st.selectbox("Origem SQL", ["mercado", "lancamentos"], key="sql_origem")
    with c2:
        sql_negocio = st.selectbox("Negócio SQL", ["venda", "aluguel"], key="sql_negocio")
    with c3:
        sql_topn = st.slider("Top tipologias", min_value=5, max_value=15, value=10)
    st.markdown('</div>', unsafe_allow_html=True)

    geo_negocio = "Venda" if sql_negocio == "venda" else "Aluguel"
    geo_tipo = st.selectbox(
        "Filtro geográfico por tipologia (normalizada)",
        ["todas"] + [
            "apartamento", "casa", "casa_de_condominio", "sobrado", "flat",
            "cobertura", "lote_terreno", "fazenda_sitios_chacaras", "imovel_comercial",
            "ponto_comercial_loja_box", "galpao_deposito_armazem", "escritorio",
            "consultorio", "predio_edificio_inteiro", "edificio_residencial"
        ],
        key="geo_tipo_cidade",
    )

    geo_city_df, _ = fetch_geo_rankings(
        lat=float(sql_lat),
        lon=float(sql_lon),
        raio=int(sql_raio),
        data_ref_sql=sql_data_ref.strip() or None,
        tipo_negocio=geo_negocio,
        tipo_imovel_norm=None if geo_tipo == "todas" else geo_tipo,
    )

    sql_df = payload_to_dataframe(
        st.session_state.get("sql_payload") or {},
        origem=sql_origem,
        negocio=sql_negocio,
    )

    if sql_df.empty:
        st.info("Sem dados SQL para os filtros/raio atuais.")
    else:
        # ── KPIs (SQL) ──
        df_kpi = sql_df.dropna(subset=["media_geral"]).copy()
        top_row = df_kpi.iloc[0] if not df_kpi.empty else None
        maior_preco = fmt_brl(top_row["media_geral"]) if top_row is not None else "R$ 0,00"
        maior_tipo = top_row["tipologia"] if top_row is not None else "-"
        media_geral = fmt_brl(df_kpi["media_geral"].mean()) if not df_kpi.empty else "R$ 0,00"
        total_tipos = int(sql_df["tipologia"].nunique())
        total_ofertas = int(sql_df["qtd_anuncios"].fillna(0).sum())

        st.markdown(
            f"""
            <div class="kpi-row">
                <div class="kpi">
                    <div class="kpi-label">Maior Preço / m²</div>
                    <div class="kpi-val">{maior_preco}</div>
                    <div class="kpi-delta">Tipologia líder: {maior_tipo}</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Média Geral m²</div>
                    <div class="kpi-val">{media_geral}</div>
                    <div class="kpi-delta">Origem: {sql_origem} · Negócio: {sql_negocio}</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Tipologias com dados</div>
                    <div class="kpi-val">{total_tipos}</div>
                    <div class="kpi-delta">Raio configurado no painel lateral</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Ofertas agregadas</div>
                    <div class="kpi-val">{total_ofertas:,}</div>
                    <div class="kpi-delta">Total de anúncios na janela</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Ranking m² ──
        st.markdown('<div class="sec-label">Ranking Comparativo</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Mediana do m² por Tipologia</div>', unsafe_allow_html=True)

        rank_df = sql_df.dropna(subset=["media_geral"]).head(sql_topn).sort_values("media_geral", ascending=True)
        fig_sql = px.bar(
            rank_df,
            x="media_geral",
            y="tipologia",
            orientation="h",
            color="disponivel",
            color_discrete_map={True: "#00E5A0", False: "#6C5CE7"},
            title="Top tipologias por mediana de valor m²",
        )
        fig_sql.update_layout(
            **PLOT_BASE,
            height=420,
            margin=dict(l=8, r=12, t=42, b=10),
            showlegend=False,
        )
        dark_axes(fig_sql, xgrid=True, ygrid=False)
        fig_sql.update_xaxes(tickprefix='R$ ', tickformat=',')
        st.plotly_chart(fig_sql, use_container_width=True)

        # ── Tabela principal SQL ──
        st.markdown(
            """
            <div class="tbl-head">
                <span class="tbl-icon">▤</span>
                <span class="tbl-title">Valorização e Liquidez por Tipologia</span>
                <span class="tbl-pill">Dados SQL parametrizados por raio</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            sql_df,
            use_container_width=True,
            hide_index=True,
            height=520,
            column_config={
                "tipologia": st.column_config.TextColumn("Tipologia", width="medium"),
                "media_geral": st.column_config.NumberColumn("Mediana m²", format="R$ %.2f"),
                "qtd_anuncios": st.column_config.NumberColumn("Qtd anúncios", format="%d"),
                "liquidez_dias": st.column_config.NumberColumn("Liquidez (dias)", format="%.0f"),
                "variacao_3m": st.column_config.NumberColumn("Var. 3m", format="%.2f%%"),
                "variacao_6m": st.column_config.NumberColumn("Var. 6m", format="%.2f%%"),
                "variacao_12m": st.column_config.NumberColumn("Var. 12m", format="%.2f%%"),
                "disponivel": st.column_config.CheckboxColumn("Disponível"),
            },
        )

        # ── Variação 3/6/12m (SQL) ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Variação por Horizonte</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Comparativo 3M · 6M · 12M por Tipologia</div>', unsafe_allow_html=True)

        var_df = (
            sql_df[["tipologia", "variacao_3m", "variacao_6m", "variacao_12m"]]
            .dropna(how="all", subset=["variacao_3m", "variacao_6m", "variacao_12m"])
            .head(8)
            .melt(id_vars="tipologia", var_name="periodo", value_name="variacao")
        )
        fig_var = px.bar(
            var_df,
            x="tipologia",
            y="variacao",
            color="periodo",
            barmode="group",
            color_discrete_map={
                "variacao_3m": "#00E5A0",
                "variacao_6m": "#6C5CE7",
                "variacao_12m": "#00B4D8",
            },
        )
        fig_var.update_layout(
            **PLOT_BASE,
            height=410,
            margin=dict(l=8, r=8, t=16, b=16),
            legend_title_text="",
        )
        dark_axes(fig_var)
        fig_var.update_yaxes(ticksuffix='%')
        st.plotly_chart(fig_var, use_container_width=True)

    # ── Cidades (join espacial com cad_mun) ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Geografia · Municípios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Preço m² por Cidade (api_mercado × geo_floripa.cad_mun)</div>', unsafe_allow_html=True)

    if geo_city_df.empty:
        st.info("Sem dados geográficos por cidade para os filtros atuais.")
    else:
        city_rank = geo_city_df.head(20).sort_values("mediana_m2", ascending=True)
        fig_city = px.bar(
            city_rank,
            x="mediana_m2",
            y="local",
            orientation="h",
            color="qtd_anuncios",
            color_continuous_scale=[[0, "#6C5CE7"], [0.5, "#00B4D8"], [1, "#00E5A0"]],
            title="Ranking de mediana m² por município",
        )
        fig_city.update_layout(
            **PLOT_BASE,
            height=460,
            margin=dict(l=8, r=12, t=42, b=10),
            coloraxis_showscale=False,
        )
        dark_axes(fig_city, xgrid=True, ygrid=False)
        fig_city.update_xaxes(tickprefix='R$ ', tickformat=',')
        st.plotly_chart(fig_city, use_container_width=True)

        st.dataframe(
            geo_city_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "local": st.column_config.TextColumn("Cidade", width="medium"),
                "qtd_anuncios": st.column_config.NumberColumn("Qtd anúncios", format="%d"),
                "mediana_m2": st.column_config.NumberColumn("Mediana m²", format="R$ %.2f"),
                "mediana_venda": st.column_config.NumberColumn("Mediana venda", format="R$ %.2f"),
                "mediana_aluguel": st.column_config.NumberColumn("Mediana aluguel", format="R$ %.2f"),
            },
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  TAB BAIRROS
# ═══════════════════════════════════════════════════════════
with tab_bairros:
    st.markdown('<div class="content">', unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Geografia · Bairros</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Preço m² por Bairro (api_mercado × geo_floripa.cad_bairro)</div>', unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        sql_negocio_2 = st.selectbox("Negócio SQL", ["venda", "aluguel"], key="sql_negocio_2")
    with b2:
        geo_tipo_2 = st.selectbox(
            "Tipologia",
            ["todas"] + [
                "apartamento", "casa", "casa_de_condominio", "sobrado", "flat",
                "cobertura", "lote_terreno", "fazenda_sitios_chacaras", "imovel_comercial",
                "ponto_comercial_loja_box", "galpao_deposito_armazem", "escritorio",
                "consultorio", "predio_edificio_inteiro", "edificio_residencial"
            ],
            key="geo_tipo_bairro",
        )
    with b3:
        top_bairros = st.slider("Top bairros", min_value=5, max_value=30, value=15)

    geo_negocio_2 = "Venda" if sql_negocio_2 == "venda" else "Aluguel"
    _, geo_bairro_df = fetch_geo_rankings(
        lat=float(sql_lat),
        lon=float(sql_lon),
        raio=int(sql_raio),
        data_ref_sql=sql_data_ref.strip() or None,
        tipo_negocio=geo_negocio_2,
        tipo_imovel_norm=None if geo_tipo_2 == "todas" else geo_tipo_2,
    )

    if not geo_bairro_df.empty:
        municipios = sorted(geo_bairro_df["municipio"].dropna().unique().tolist())
    else:
        municipios = []

    municipio_sel = st.selectbox(
        "Município",
        ["todos"] + municipios,
        key="municipio_bairro_sel",
    )

    if municipio_sel != "todos":
        geo_bairro_df = geo_bairro_df[geo_bairro_df["municipio"] == municipio_sel].copy()

    if geo_bairro_df.empty:
        st.info("Sem dados geográficos por bairro para os filtros atuais.")
    else:
        bairro_rank = geo_bairro_df.head(top_bairros).sort_values("mediana_m2", ascending=True)
        fig_bairro = px.bar(
            bairro_rank,
            x="mediana_m2",
            y="local",
            orientation="h",
            color="qtd_anuncios",
            color_continuous_scale=[[0, "#6C5CE7"], [0.5, "#00B4D8"], [1, "#00E5A0"]],
            title="Ranking de mediana m² por bairro",
        )
        fig_bairro.update_layout(
            **PLOT_BASE,
            height=480,
            margin=dict(l=8, r=10, t=42, b=10),
            coloraxis_showscale=False,
        )
        dark_axes(fig_bairro, xgrid=True, ygrid=False)
        fig_bairro.update_xaxes(tickprefix='R$ ', tickformat=',')
        st.plotly_chart(fig_bairro, use_container_width=True)

        st.markdown(
            """
            <div class="tbl-head">
                <span class="tbl-icon">▤</span>
                <span class="tbl-title">Detalhamento por Bairro</span>
                <span class="tbl-pill">Contenção espacial via ST_Contains</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            geo_bairro_df[["municipio", "local", "qtd_anuncios", "mediana_m2"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "municipio": st.column_config.TextColumn("Cidade", width="medium"),
                "local": st.column_config.TextColumn("Bairro", width="medium"),
                "qtd_anuncios": st.column_config.NumberColumn("Qtd anúncios", format="%d"),
                "mediana_m2": st.column_config.NumberColumn("Mediana m²", format="R$ %.2f"),
            },
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="loc-footer">
    <div>
        <h5>Base de Dados</h5>
        <p>O Índice LOCATES analisa mensalmente mais de 10.000 ofertas ativas
        nos principais canais imobiliários de Santa Catarina, abrangendo
        apartamentos e casas residenciais.</p>
    </div>
    <div>
        <h5>Tratamento Estatístico</h5>
        <p>Os valores representam a mediana dos preços por m² privativo.
        São aplicados filtros estatísticos rigorosos para remoção de distorções
        e garantir a precisão das tendências.</p>
    </div>
</div>
<div class="loc-copy">© 2024 LOCATES INTELIGÊNCIA IMOBILIÁRIA · Florianópolis, SC</div>
""", unsafe_allow_html=True)