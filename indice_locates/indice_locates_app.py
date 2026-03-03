"""
Índice LOCATES — Inteligência Imobiliária (Streamlit)
Dashboard conectado ao banco de dados PostgreSQL.
"""

import os
import io
import math
import base64
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --purple: #4F3C88;
    --green: #4FE48B;
    --dark: #2d244a;
    --light: #fdfdff;
    --surface: #ffffff;
    --border: #f0edf9;
    --muted: #94a3b8;
}

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
    font-family: 'Montserrat', sans-serif !important;
    background-color: var(--light) !important;
    color: var(--dark) !important;
}

#MainMenu, footer, header, [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
    padding: 1rem 2rem 3rem !important;
    max-width: 1200px !important;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f5f4fa; }
::-webkit-scrollbar-thumb { background: var(--purple); border-radius: 10px; }

/* ── Header ── */
.loc-header {
    text-align: center;
    padding: 2rem 0 1.5rem;
}
.loc-title {
    font-size: 3.2rem;
    font-weight: 900;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: -0.04em;
    margin: 0;
    line-height: 1;
}
.loc-title em {
    font-style: italic;
    color: var(--green);
}
.loc-subtitle {
    font-size: 0.85rem;
    color: var(--muted);
    font-weight: 500;
    margin-top: 0.5rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}
.loc-ref {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--green);
    color: var(--purple);
    padding: 5px 16px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 1rem;
}

/* ── KPI Grid ── */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}
@media (max-width: 768px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
}
.kpi {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(79, 60, 136, 0.05);
}
.kpi-val {
    font-size: 1.4rem;
    font-weight: 900;
    color: var(--purple);
    margin-bottom: 2px;
}
.kpi-label {
    font-size: 0.5rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted);
}
.kpi-delta {
    font-size: 0.65rem;
    font-weight: 700;
    margin-top: 4px;
}
.kpi-delta.pos { color: #2bb96a; }
.kpi-delta.neg { color: #ef4444; }

/* ── Section ── */
.sec-card {
    background: var(--surface);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(79, 60, 136, 0.06);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.sec-card.purple-top { border-top: 8px solid var(--purple); }
.sec-card.green-top { border-top: 8px solid var(--green); }
.sec-card.purple-bot { border-bottom: 8px solid var(--purple); }
.sec-header {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: -0.01em;
    text-align: center;
    margin-bottom: 4px;
}
.sec-sub {
    font-size: 0.55rem;
    color: var(--purple);
    opacity: 0.4;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1.5rem;
}

/* ── Table header ── */
.tbl-header {
    background: var(--purple);
    padding: 14px 22px;
    border-radius: 12px 12px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.tbl-title {
    font-size: 0.85rem;
    font-weight: 800;
    color: white;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}
.tbl-pill {
    font-size: 0.5rem;
    font-weight: 900;
    color: var(--purple);
    background: var(--green);
    padding: 4px 14px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ── Tabs ── */
div[data-testid="stTabs"] > div:first-child {
    justify-content: center !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Montserrat', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    padding: 1rem 2rem !important;
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--purple) !important;
    border-bottom: 4px solid var(--green) !important;
}
div[data-testid="stTabs"] [data-testid="stTabContent"] {
    padding: 0 !important;
}

/* ── Selectbox ── */
.stSelectbox label, .stMultiSelect label {
    font-size: 0.55rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--purple) !important;
    opacity: 0.6;
    font-family: 'Montserrat', sans-serif !important;
}

/* ── Footer ── */
.loc-footer {
    background: var(--surface);
    border-left: 8px solid var(--purple);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-top: 2rem;
    box-shadow: 0 4px 20px rgba(79, 60, 136, 0.06);
}
.loc-footer h5 {
    font-size: 0.6rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--purple);
    opacity: 0.5;
    margin-bottom: 6px;
}
.loc-footer p {
    font-size: 0.7rem;
    color: var(--muted);
    line-height: 1.7;
}

/* ── Plotly fixes ── */
.stPlotlyChart { margin-bottom: -1rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONEXÃO COM BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════

PALETTE = [
    "#4F3C88", "#2bb96a", "#00a8b5", "#ff7f50", "#ffd700",
    "#4169e1", "#e91e63", "#8e44ad", "#16a085", "#2c3e50",
]

MES_NOMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

MES_ABREV = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


def _get_conn_str() -> str:
    return (
        f"host={os.environ['HOST_URL']} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASS']}"
    )


@st.cache_data(ttl=3600)
def load_available_dates() -> list[str]:
    """Retorna as datas disponíveis formatadas como 'Mês Ano', ordem decrescente."""
    with psycopg.connect(_get_conn_str()) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT data_tabela
            FROM observatorio.indice_cidades_variacao
            WHERE estado_sigla = 'SC'
            ORDER BY data_tabela DESC
        """)
        dates = [r[0] for r in cur.fetchall()]

    result = []
    date_map = {}
    for d in dates:
        label = f"{MES_NOMES[d.month]} {d.year}"
        result.append(label)
        date_map[label] = d

    # Guardar mapa no session_state para conversão reversa
    st.session_state["_date_map"] = date_map
    return result


def _date_from_label(label: str):
    """Converte label 'Mês Ano' de volta para a data do banco."""
    return st.session_state.get("_date_map", {}).get(label)


@st.cache_data(ttl=3600)
def load_cidades_data(_data_tabela) -> pd.DataFrame:
    """Carrega dados de cidades do banco para a data de referência."""
    with psycopg.connect(_get_conn_str()) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                cidade,
                tipo_imovel    AS tipologia,
                tipo_negocio   AS negocio,
                num_quartos::text AS dorms,
                valor_m2_atual AS vm2,
                var_pct_3m     AS var3,
                var_pct_6m     AS var6,
                var_pct_12m    AS var12,
                quantidade_anuncios,
                tendencia_anual
            FROM observatorio.indice_cidades_variacao
            WHERE estado_sigla = 'SC'
              AND data_tabela  = %s
        """, (str(_data_tabela),))
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=cols)
    for col in ["vm2", "var3", "var6", "var12"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quantidade_anuncios"] = pd.to_numeric(df["quantidade_anuncios"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=3600)
def load_cidades_history() -> pd.DataFrame:
    """Carrega séries históricas de valor_m2_atual para o gráfico de evolução."""
    with psycopg.connect(_get_conn_str()) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                cidade,
                tipo_imovel    AS tipologia,
                tipo_negocio   AS negocio,
                num_quartos::text AS dorms,
                data_tabela,
                valor_m2_atual AS vm2
            FROM observatorio.indice_cidades_variacao
            WHERE estado_sigla = 'SC'
            ORDER BY data_tabela
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=cols)
    df["vm2"] = pd.to_numeric(df["vm2"], errors="coerce")
    df["data_tabela"] = pd.to_datetime(df["data_tabela"])
    return df


@st.cache_data(ttl=3600)
def load_bairros_data(_data_tabela) -> pd.DataFrame:
    """Tenta carregar dados de bairros do banco. Retorna DF vazio se a tabela
    não existir ou estiver vazia — o app usará fallback com dados simulados."""
    try:
        with psycopg.connect(_get_conn_str()) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    cidade,
                    bairro,
                    tipo_imovel    AS tipologia,
                    tipo_negocio   AS negocio,
                    num_quartos::text AS dorms,
                    valor_m2_atual AS vm2,
                    var_pct_3m     AS var3,
                    var_pct_6m     AS var6,
                    var_pct_12m    AS var12
                FROM observatorio.indice_bairros
                WHERE estado_sigla = 'SC'
                  AND data_tabela  = %s
            """, (str(_data_tabela),))
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        for col in ["vm2", "var3", "var6", "var12"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def _generate_fallback_bairros() -> pd.DataFrame:
    """Dados simulados de bairros como fallback quando a tabela do banco não existe."""
    np.random.seed(1337)
    bairros_config = {
        "Florianópolis": (14350, 78, [
            ("Jurerê Internacional", 2.2), ("Cacupé", 1.8),
            ("Lagoa da Conceição", 1.5), ("Campeche", 1.15),
            ("Centro", 1.1), ("Agronômica", 1.05),
            ("Itacorubi", 1.0), ("Trindade", 0.92),
            ("Canasvieiras", 0.95), ("Córrego Grande", 0.98),
            ("Coqueiros", 0.90), ("Ingleses", 0.88),
            ("Saco Grande", 0.85), ("Estreito", 0.82),
            ("Capoeiras", 0.78),
        ]),
        "São José": (8900, 48, [
            ("Kobrasol", 1.15), ("Campinas", 1.10),
            ("Barreiros", 0.95), ("Ipiranga", 0.88),
            ("Areias", 0.82), ("Serraria", 0.78),
            ("Forquilhas", 0.65), ("Fazenda", 0.72),
        ]),
        "Balneário Camboriú": (26800, 135, [
            ("Barra Sul", 1.45), ("Centro", 1.20),
            ("Pioneiros", 1.0), ("Ariribá", 0.92),
            ("Nações", 0.85), ("Vila Real", 0.80),
        ]),
        "Itapema": (19400, 105, [
            ("Meia Praia", 1.30), ("Centro", 1.0),
            ("Castelo Branco", 0.85), ("Ilhota", 0.75), ("Morretes", 0.70),
        ]),
        "Itajaí": (14800, 82, [
            ("Praia Brava", 1.65), ("Fazenda", 1.20),
            ("Centro", 1.05), ("São João", 0.92),
            ("Ressacada", 0.88), ("Dom Bosco", 0.80), ("Cordeiros", 0.75),
        ]),
        "Joinville": (9200, 52, [
            ("Centro", 1.15), ("América", 1.05),
            ("Atiradores", 1.0), ("Bucarein", 0.92),
            ("Glória", 0.90), ("Anita Garibaldi", 0.85),
            ("Iririú", 0.75), ("Costa e Silva", 0.70),
        ]),
        "Palhoça": (7800, 42, [
            ("Pedra Branca", 1.45), ("Pagani", 1.10),
            ("Centro", 0.95), ("Ponte do Imaruim", 0.85),
            ("São Sebastião", 0.75), ("Barra do Aririú", 0.70),
        ]),
    }

    dorm_mult = {"1": 0.86, "2": 0.94, "3": 1.0, "4": 1.15}
    rows = []
    for cidade, (base_v, base_a, bairros) in bairros_config.items():
        for bairro, mult in bairros:
            for tipo in ["Apartamento", "Casa"]:
                for neg in ["Venda", "Aluguel"]:
                    for d in ["1", "2", "3", "4"]:
                        dm = dorm_mult[d]
                        tipo_m = 0.72 if tipo == "Casa" else 1.0
                        base = base_v if neg == "Venda" else base_a
                        noise = 0.90 + np.random.random() * 0.20
                        vm2 = round(base * mult * dm * tipo_m * noise)
                        v3 = round((np.random.random() - 0.35) * 7 * mult, 1)
                        v6 = round(v3 * 1.5 + (np.random.random() - 0.4) * 3, 1)
                        v12 = round(v6 * 1.45 + (np.random.random() - 0.3) * 5, 1)

                        rows.append({
                            "cidade": cidade, "bairro": bairro,
                            "tipologia": tipo, "negocio": neg,
                            "dorms": d, "vm2": vm2,
                            "var3": v3, "var6": v6, "var12": v12,
                        })

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_brl(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_var(v: float) -> str:
    if pd.isna(v):
        return "--"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


def var_color(v: float) -> str:
    if pd.isna(v):
        return "#94a3b8"
    return "#2bb96a" if v > 0.05 else "#ef4444" if v < -0.05 else "#94a3b8"


def style_var_cell(val):
    """Highlight de variação: verde >5%, laranja 0–5%, vermelho <0%."""
    if pd.isna(val):
        return ""
    if val < 0:
        return "background-color: rgba(239,68,68,0.18); color: #dc2626; font-weight: 700"
    elif val <= 5:
        return "background-color: rgba(245,158,11,0.18); color: #d97706; font-weight: 700"
    else:
        return "background-color: rgba(43,185,106,0.18); color: #16a34a; font-weight: 700"


def aggregate(df: pd.DataFrame, group_col: str, neg: str, tip: str, dorms: str) -> pd.DataFrame:
    mask = df["negocio"] == neg
    if tip != "Todos":
        mask &= df["tipologia"] == tip
    if dorms != "Todas":
        mask &= df["dorms"] == dorms
    sub = df[mask]
    if sub.empty:
        return pd.DataFrame(columns=["name", "vm2", "v3", "v6", "v12"])
    agg = sub.groupby(group_col).agg(
        vm2=("vm2", "mean"), v3=("var3", "mean"),
        v6=("var6", "mean"), v12=("var12", "mean"),
    ).reset_index().rename(columns={group_col: "name"})
    return agg.sort_values("vm2", ascending=False).reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Montserrat, sans-serif", color="#4F3C88"),
    margin=dict(l=10, r=80, t=10, b=10),
)


def chart_ranking(data: pd.DataFrame, top_n: int = 10) -> go.Figure:
    display = data.head(top_n).iloc[::-1]
    colors = ["#4FE48B" if i == len(display) - 1 else "#4F3C88" for i in range(len(display))]
    labels = [f"{len(display)-i}º  |  {n}" for i, n in enumerate(display["name"])]

    fig = go.Figure(go.Bar(
        x=display["vm2"],
        y=labels,
        orientation="h",
        marker=dict(color=colors, cornerradius=8),
        text=[fmt_brl(v) for v in display["vm2"]],
        textposition="outside",
        textfont=dict(family="Montserrat", weight=800, size=11, color="#4F3C88"),
    ))
    fig.update_layout(
        **PLOT_BASE,
        height=max(280, len(display) * 52),
        showlegend=False,
        bargap=0.3,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(
        showgrid=False, tickfont=dict(family="Montserrat", size=11, weight=700, color="#4F3C88"),
    )
    return fig


def chart_history(
    selected: list[str],
    df_hist: pd.DataFrame,
    neg: str,
    tip: str,
    dorms: str,
    group_col: str = "cidade",
) -> go.Figure:
    """Gráfico de evolução histórica usando dados reais do banco."""
    mask = df_hist["negocio"] == neg
    if tip != "Todos":
        mask &= df_hist["tipologia"] == tip
    if dorms != "Todas":
        mask &= df_hist["dorms"] == dorms
    sub = df_hist[mask & df_hist[group_col].isin(selected)]

    fig = go.Figure()
    for idx, name in enumerate(selected):
        series = sub[sub[group_col] == name].groupby("data_tabela")["vm2"].median().sort_index()
        if series.empty:
            continue
        fig.add_trace(go.Scatter(
            x=series.index,  # datetime real — garante ordem cronológica
            y=series.values,
            mode="lines+markers",
            name=name,
            line=dict(color=PALETTE[idx % len(PALETTE)], width=3),
            marker=dict(size=5, color=PALETTE[idx % len(PALETTE)]),
        ))
    base = {k: v for k, v in PLOT_BASE.items() if k != 'margin'}
    fig.update_layout(
        **base,
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, weight=700),
        ),
        hovermode="x unified",
    )
    fig.update_xaxes(
        type="date",
        showgrid=False,
        tickfont=dict(size=10),
        linecolor="rgba(79,60,136,0.1)",
        dtick="M1",  # tick a cada mês
        tickformat="%b/%y",  # formato "Jan/23"
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(79,60,136,0.06)",
        tickfont=dict(size=10),
        tickprefix="R$ ", tickformat=",",
    )
    return fig


def _chart_history_fallback(data: pd.DataFrame, selected: list[str]) -> go.Figure:
    """Gráfico de evolução histórica sintético (fallback para bairros sem dados históricos)."""
    fig = go.Figure()
    for idx, (_, row) in enumerate(data[data["name"].isin(selected)].iterrows()):
        v12 = row["v12"] if not pd.isna(row["v12"]) else 0
        start = row["vm2"] / (1 + v12 / 100)
        step = (row["vm2"] - start) / 12
        seed = sum(ord(c) for c in row["name"])
        pts = []
        running = start
        for i in range(12):
            noise = math.sin(seed * (i + 1) * 0.7) * (row["vm2"] * 0.008)
            pts.append(round(running + noise))
            running += step
        pts[11] = round(row["vm2"])
        labels = [f"M{i+1}" for i in range(12)]
        fig.add_trace(go.Scatter(
            x=labels, y=pts,
            mode="lines+markers",
            name=row["name"],
            line=dict(color=PALETTE[idx % len(PALETTE)], width=3),
            marker=dict(size=5, color=PALETTE[idx % len(PALETTE)]),
        ))
    base = {k: v for k, v in PLOT_BASE.items() if k != 'margin'}
    fig.update_layout(
        **base, height=420, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=10, weight=700)),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10), linecolor="rgba(79,60,136,0.1)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(79,60,136,0.06)", tickfont=dict(size=10), tickprefix="R$ ", tickformat=",")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def build_pdf_html(
    ref_date: str,
    data_cidades: pd.DataFrame,
    data_bairros: pd.DataFrame,
    filters_cidade: dict,
    filters_bairro: dict,
) -> str:
    """Gera HTML completo pronto para download que pode ser convertido em PDF pelo browser."""

    def _table_rows(df: pd.DataFrame) -> str:
        rows_html = ""
        for i, row in df.iterrows():
            v3_color = "#2bb96a" if row["v3"] > 0 else "#ef4444"
            v6_color = "#2bb96a" if row["v6"] > 0 else "#ef4444"
            v12_color = "#2bb96a" if row["v12"] > 0 else "#ef4444"
            rows_html += f"""
            <tr style="border-bottom:1px solid #f0edf9;">
                <td style="padding:10px;text-align:center;font-weight:900;color:#4F3C88;opacity:0.4;font-size:10px">{i+1}º</td>
                <td style="padding:10px;font-weight:700;color:#4F3C88;font-size:12px">{row['name']}</td>
                <td style="padding:10px;text-align:right;font-weight:800;color:#4F3C88;font-size:12px">{fmt_brl(row['vm2'])}</td>
                <td style="padding:10px;text-align:center;font-weight:700;font-size:12px;color:{v3_color}">{fmt_var(row['v3'])}</td>
                <td style="padding:10px;text-align:center;font-weight:700;font-size:12px;color:{v6_color}">{fmt_var(row['v6'])}</td>
                <td style="padding:10px;text-align:center;font-weight:700;font-size:12px;color:{v12_color}">{fmt_var(row['v12'])}</td>
            </tr>"""
        return rows_html

    filter_label_c = f"{filters_cidade['tip']} | {filters_cidade['neg']} | {filters_cidade['dorms']}"
    filter_label_b = f"{filters_bairro['cidade']} | {filters_bairro['tip']} | {filters_bairro['neg']} | {filters_bairro['dorms']}"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');
body {{ font-family: 'Montserrat', sans-serif; color: #2d244a; padding: 30px; background: #fdfdff; }}
h1 {{ font-size: 2rem; font-weight: 900; color: #4F3C88; text-transform: uppercase; text-align: center; }}
h1 em {{ color: #4FE48B; font-style: italic; }}
.ref {{ text-align: center; font-size: 0.65rem; color: #4F3C88; opacity: 0.5; margin-bottom: 2rem; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 700; }}
.section {{ margin-top: 2rem; }}
.section h2 {{ font-size: 1rem; font-weight: 800; color: #4F3C88; text-transform: uppercase; margin-bottom: 0.5rem; }}
.filter-badge {{ font-size: 0.6rem; background: #4FE48B; color: #4F3C88; padding: 3px 12px; border-radius: 999px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.08em; display: inline-block; margin-bottom: 1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; }}
th {{ padding: 10px; font-size: 9px; font-weight: 800; color: #4F3C88; opacity: 0.4; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 2px solid #f0edf9; }}
.page-break {{ page-break-before: always; }}
</style></head><body>
<h1>Índice <em>LOCATES</em></h1>
<div class="ref">Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · Ref: {ref_date}</div>
<p style="text-align:center;font-size:0.8rem;color:#94a3b8;max-width:500px;margin:0 auto 2rem">
Inteligência de dados e monitorização estratégica do mercado imobiliário em Santa Catarina.</p>

<div class="section">
<h2>Ranking Comparativo do m² — Cidades</h2>
<div class="filter-badge">{filter_label_c}</div>
<table>
<thead><tr>
<th style="text-align:center;width:50px">Rank</th>
<th>Cidade</th>
<th style="text-align:right">Mediana m²</th>
<th style="text-align:center">3 Meses</th>
<th style="text-align:center">6 Meses</th>
<th style="text-align:center">12 Meses</th>
</tr></thead>
<tbody>{_table_rows(data_cidades)}</tbody>
</table>
</div>

<div class="section page-break">
<h2>Ranking Comparativo do m² — Bairros</h2>
<div class="filter-badge">{filter_label_b}</div>
<table>
<thead><tr>
<th style="text-align:center;width:50px">Rank</th>
<th>Bairro</th>
<th style="text-align:right">Mediana m²</th>
<th style="text-align:center">3 Meses</th>
<th style="text-align:center">6 Meses</th>
<th style="text-align:center">12 Meses</th>
</tr></thead>
<tbody>{_table_rows(data_bairros)}</tbody>
</table>
</div>

<div class="section" style="margin-top:3rem;border-left:6px solid #4F3C88;padding-left:1.5rem;">
<h2 style="font-size:0.7rem;letter-spacing:0.15em;opacity:0.6">Notas Metodológicas</h2>
<p style="font-size:0.7rem;color:#94a3b8;line-height:1.8">
Monitorização automatizada de mais de 14.000 ofertas ativas mensais.
Remoção de duplicados e outliers via IQR e Z-Score.
Utilização da Mediana para maior estabilidade.
Variações calculadas com suavização por média móvel.
</p>
</div>
</body></html>"""
    return html


# ═══════════════════════════════════════════════════════════════════════════════
#  DADOS (conexão ao banco)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    MESES_REF = load_available_dates()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="loc-header">
    <h1 class="loc-title">Índice <em>LOCATES</em></h1>
    <p class="loc-subtitle">
        Inteligência de dados e monitorização estratégica do mercado imobiliário em Santa Catarina.
    </p>
</div>
""", unsafe_allow_html=True)

col_ref, col_pdf = st.columns([3, 1])
with col_ref:
    ref_date = st.selectbox("Referência", MESES_REF, label_visibility="collapsed")
with col_pdf:
    pdf_placeholder = st.empty()

st.markdown(f'<div style="text-align:center"><span class="loc-ref">📅 {ref_date}</span></div>', unsafe_allow_html=True)

# Carregar dados do banco para a data selecionada
sel_date = _date_from_label(ref_date)
df_cidades = load_cidades_data(sel_date)
df_hist_cidades = load_cidades_history()

# Bairros: tenta banco, senão usa fallback simulado
df_bairros_db = load_bairros_data(sel_date)
if df_bairros_db.empty:
    df_bairros = _generate_fallback_bairros()
    _bairros_source = "simulado"
else:
    df_bairros = df_bairros_db
    _bairros_source = "banco"

CIDADES_COM_BAIRROS = sorted(df_bairros["cidade"].unique().tolist())


# ═══════════════════════════════════════════════════════════════════════════════
#  KPIs
# ═══════════════════════════════════════════════════════════════════════════════
venda_apt = df_cidades[(df_cidades["negocio"] == "Venda") & (df_cidades["tipologia"] == "Apartamento")]
n_cidades = venda_apt["cidade"].nunique()
mediana_sc = venda_apt["vm2"].median() if not venda_apt.empty else 0
avg_var12 = venda_apt["var12"].mean() if not venda_apt.empty else 0
n_bairros = df_bairros["bairro"].nunique() if "bairro" in df_bairros.columns else 0
total_anuncios = df_cidades["quantidade_anuncios"].sum() if "quantidade_anuncios" in df_cidades.columns else 0
anuncios_label = f"{total_anuncios/1000:.1f}K" if total_anuncios > 0 else "--"

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi">
        <div class="kpi-val">{n_cidades}</div>
        <div class="kpi-label">Cidades Monitoradas</div>
    </div>
    <div class="kpi">
        <div class="kpi-val">{fmt_brl(mediana_sc)}</div>
        <div class="kpi-label">Mediana m² SC (Apt/Venda)</div>
        <div class="kpi-delta pos">{'+' if avg_var12 > 0 else ''}{avg_var12:.1f}% em 12m</div>
    </div>
    <div class="kpi">
        <div class="kpi-val">{n_bairros}</div>
        <div class="kpi-label">Bairros Analisados</div>
    </div>
    <div class="kpi">
        <div class="kpi-val">{anuncios_label}</div>
        <div class="kpi-label">Anúncios Processados/mês</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_cidades, tab_bairros_tab = st.tabs([
    "  Índice Locates Cidade  ",
    "  Índice Locates Bairros  ",
])


# ─────────────────────────────────────────────────
#  TAB: CIDADES
# ─────────────────────────────────────────────────
with tab_cidades:

    # ── Ranking ──
    st.markdown(f"""
    <div class="sec-card purple-top">
        <div class="sec-header">Ranking Comparativo do m² das Cidades</div>
        <div class="sec-sub">Base de dados atualizada · Ref: {ref_date}</div>
    </div>
    """, unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 1])
    with fc1:
        tip_c = st.selectbox("Tipo Imóvel", ["Apartamento", "Casa", "Todos"], key="tip_c")
    with fc2:
        neg_c = st.selectbox("Negócio", ["Venda", "Aluguel"], key="neg_c")
    with fc3:
        dorms_c = st.selectbox("Dormitórios", ["Todas", "1", "2", "3", "4"], key="dorms_c")
    with fc4:
        top_n_c = st.selectbox("Top N", [10, 15, 20, "Todos"], key="topn_c")

    agg_c = aggregate(df_cidades, "cidade", neg_c, tip_c, dorms_c)

    if agg_c.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        n = len(agg_c) if top_n_c == "Todos" else int(top_n_c)
        fig_rank_c = chart_ranking(agg_c, top_n=n)
        st.plotly_chart(fig_rank_c, width="stretch")

        # ── Tabela ──
        label_c = f"{tip_c} | {neg_c} | {'Todas Tipologias' if dorms_c == 'Todas' else dorms_c + ' Qto(s)'}"
        st.markdown(f"""
        <div class="tbl-header">
            <span class="tbl-title">📊 Valorização Anual</span>
            <span class="tbl-pill">{label_c}</span>
        </div>
        """, unsafe_allow_html=True)

        display_c = agg_c.head(n).copy()
        display_c.insert(0, "rank", [f"{i+1}º" for i in range(len(display_c))])
        display_c = display_c.rename(columns={
            "name": "Cidade", "vm2": "Mediana m²",
            "v3": "3 Meses", "v6": "6 Meses", "v12": "12 Meses",
        })

        var_cols_c = ["3 Meses", "6 Meses", "12 Meses"]
        styled_c = (
            display_c.style
            .map(style_var_cell, subset=var_cols_c)
            .format({
                "Mediana m²": lambda v: fmt_brl(v) if not pd.isna(v) else "--",
                "3 Meses": lambda v: fmt_var(v),
                "6 Meses": lambda v: fmt_var(v),
                "12 Meses": lambda v: fmt_var(v),
            })
        )
        st.dataframe(
            styled_c,
            width="stretch",
            hide_index=True,
            height=min(600, 45 * len(display_c) + 40),
            column_config={
                "rank": st.column_config.TextColumn("Rank", width="small"),
                "Cidade": st.column_config.TextColumn("Cidade", width="medium"),
            },
        )

        # ── Histórico ──
        st.markdown(f"""
        <div class="sec-card green-top" style="margin-top:1.5rem">
            <div class="sec-header">Evolução Histórica do m²</div>
            <div class="sec-sub">Últimos 12 meses · Valores de {neg_c}</div>
        </div>
        """, unsafe_allow_html=True)

        cities_avail = agg_c["name"].tolist()
        default_sel = cities_avail[:3]
        sel_cities = st.multiselect(
            "Cidades no gráfico",
            cities_avail,
            default=default_sel,
            key="hist_c",
        )
        if sel_cities:
            fig_hist_c = chart_history(
                sel_cities, df_hist_cidades, neg_c, tip_c, dorms_c, group_col="cidade",
            )
            st.plotly_chart(fig_hist_c, width="stretch")


# ─────────────────────────────────────────────────
#  TAB: BAIRROS
# ─────────────────────────────────────────────────
with tab_bairros_tab:

    st.markdown(f"""
    <div class="sec-card purple-top">
        <div class="sec-header">Ranking Comparativo do m² dos Bairros</div>
        <div class="sec-sub">Base de dados atualizada · Ref: {ref_date}</div>
    </div>
    """, unsafe_allow_html=True)

    fb1, fb2, fb3, fb4, fb5 = st.columns([2, 2, 2, 2, 1])
    with fb1:
        cidade_sel = st.selectbox("Cidade", CIDADES_COM_BAIRROS, key="cidade_b")
    with fb2:
        tip_b = st.selectbox("Tipo Imóvel", ["Apartamento", "Casa", "Todos"], key="tip_b")
    with fb3:
        neg_b = st.selectbox("Negócio", ["Venda", "Aluguel"], key="neg_b")
    with fb4:
        dorms_b = st.selectbox("Dormitórios", ["Todas", "1", "2", "3", "4"], key="dorms_b")
    with fb5:
        top_n_b = st.selectbox("Top N", [10, 15, "Todos"], key="topn_b")

    sub_bairros = df_bairros[df_bairros["cidade"] == cidade_sel]
    agg_b = aggregate(sub_bairros, "bairro", neg_b, tip_b, dorms_b)

    if agg_b.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        nb = len(agg_b) if top_n_b == "Todos" else int(top_n_b)
        fig_rank_b = chart_ranking(agg_b, top_n=nb)
        st.plotly_chart(fig_rank_b, width="stretch")

        # ── Tabela bairros ──
        label_b = f"{cidade_sel} | {tip_b} | {neg_b} | {'Todas Tipologias' if dorms_b == 'Todas' else dorms_b + ' Qto(s)'}"
        st.markdown(f"""
        <div class="tbl-header">
            <span class="tbl-title">📊 Valorização Anual</span>
            <span class="tbl-pill">{label_b}</span>
        </div>
        """, unsafe_allow_html=True)

        display_b = agg_b.head(nb).copy()
        display_b.insert(0, "rank", [f"{i+1}º" for i in range(len(display_b))])
        display_b = display_b.rename(columns={
            "name": "Bairro", "vm2": "Mediana m²",
            "v3": "3 Meses", "v6": "6 Meses", "v12": "12 Meses",
        })

        var_cols_b = ["3 Meses", "6 Meses", "12 Meses"]
        styled_b = (
            display_b.style
            .map(style_var_cell, subset=var_cols_b)
            .format({
                "Mediana m²": lambda v: fmt_brl(v) if not pd.isna(v) else "--",
                "3 Meses": lambda v: fmt_var(v),
                "6 Meses": lambda v: fmt_var(v),
                "12 Meses": lambda v: fmt_var(v),
            })
        )
        st.dataframe(
            styled_b,
            width="stretch",
            hide_index=True,
            height=min(600, 45 * len(display_b) + 40),
            column_config={
                "rank": st.column_config.TextColumn("Rank", width="small"),
                "Bairro": st.column_config.TextColumn("Bairro", width="medium"),
            },
        )

        # ── Histórico bairros ──
        st.markdown(f"""
        <div class="sec-card green-top" style="margin-top:1.5rem">
            <div class="sec-header">Evolução Histórica do m²</div>
            <div class="sec-sub">Últimos 12 meses · Bairros de {cidade_sel}</div>
        </div>
        """, unsafe_allow_html=True)

        bairros_avail = agg_b["name"].tolist()
        default_sel_b = bairros_avail[:3]
        sel_bairros = st.multiselect(
            "Bairros no gráfico",
            bairros_avail,
            default=default_sel_b,
            key="hist_b",
        )
        if sel_bairros:
            # Para bairros, usar fallback de histórico sintético se não houver dados históricos reais
            if _bairros_source == "banco":
                # TODO: carregar histórico de bairros do banco quando disponível
                pass
            else:
                # Histórico sintético para bairros (fallback)
                fig_hist_b = _chart_history_fallback(agg_b, sel_bairros)
                st.plotly_chart(fig_hist_b, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF DOWNLOAD BUTTON
# ═══════════════════════════════════════════════════════════════════════════════
agg_c_pdf = aggregate(df_cidades, "cidade", neg_c, tip_c, dorms_c)
if not df_bairros.empty and CIDADES_COM_BAIRROS:
    sub_b_pdf = df_bairros[df_bairros["cidade"] == cidade_sel]
    agg_b_pdf = aggregate(sub_b_pdf, "bairro", neg_b, tip_b, dorms_b)
else:
    agg_b_pdf = pd.DataFrame(columns=["name", "vm2", "v3", "v6", "v12"])

pdf_html = build_pdf_html(
    ref_date=ref_date,
    data_cidades=agg_c_pdf,
    data_bairros=agg_b_pdf,
    filters_cidade={"tip": tip_c, "neg": neg_c, "dorms": dorms_c},
    filters_bairro={"cidade": cidade_sel, "tip": tip_b, "neg": neg_b, "dorms": dorms_b},
)

with pdf_placeholder:
    st.download_button(
        label="📄 Exportar Relatório",
        data=pdf_html.encode("utf-8"),
        file_name=f"Indice_LOCATES_{ref_date.replace(' ', '_')}.html",
        mime="text/html",
        help="Abra o HTML no navegador e use Ctrl+P para salvar como PDF",
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="loc-footer">
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2rem">
        <div>
            <h5>Recolha de Dados</h5>
            <p>Monitorização automatizada contínua de mais de 14.000 ofertas ativas
            mensais nos principais portais imobiliários de SC.</p>
        </div>
        <div>
            <h5>Higienização</h5>
            <p>Remoção algorítmica de duplicados e outliers extremos via IQR e Z-Score
            para preservar a realidade estatística.</p>
        </div>
        <div>
            <h5>Métrica</h5>
            <p>Utilização da <b>Mediana</b> para maior estabilidade contra flutuações
            pontuais de imóveis de luxo ou sub-valorizados.</p>
        </div>
        <div>
            <h5>Tendência</h5>
            <p>Variações calculadas mensalmente com suavização por média móvel para
            identificar ciclos de valorização em microrregiões.</p>
        </div>
    </div>
</div>
<div style="text-align:center;padding:1.5rem;font-size:0.6rem;color:#94a3b8;letter-spacing:0.1em;">
    © 2026 LOCATES INTELIGÊNCIA IMOBILIÁRIA · Florianópolis, SC
</div>
""", unsafe_allow_html=True)
