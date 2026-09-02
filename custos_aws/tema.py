"""Tema visual do painel: superfície escura da Locates + paleta categórica validada.

A moldura (fundo, títulos, acentos de UI) usa as cores da marca — roxo #504088,
verde #35d07e. As séries usam a paleta categórica de referência da skill de dataviz,
validada contra a superfície #16161c (banda de luminosidade, piso de croma, separação
para daltonismo, piso de visão normal e contraste ≥ 3:1 — todos passam).

Cor segue a entidade, nunca o ranking do filtro: `mapa_cores()` fixa a atribuição a
partir do ranking do período inteiro, então filtrar não repinta as séries.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# ── superfícies e tinta ───────────────────────────────────────────────────────
PLANO = "#0d0d10"        # fundo da página
SUPERFICIE = "#16161c"   # superfície dos gráficos
TINTA = "#f7f8fa"        # tinta primária
TINTA_2 = "#c3c2b7"      # tinta secundária
TINTA_MUDA = "#898781"   # eixos e rótulos
GRADE = "#2c2c2a"        # gridline (sólida, discreta)
BASE = "#383835"         # linha de base

# ── marca ─────────────────────────────────────────────────────────────────────
ROXO = "#504088"
VERDE = "#35d07e"

# ── paleta categórica (dark, validada em #16161c) ─────────────────────────────
SERIES = [
    "#3987e5",  # 1 azul
    "#d95926",  # 2 laranja
    "#199e70",  # 3 aqua
    "#c98500",  # 4 amarelo
    "#d55181",  # 5 magenta
    "#008300",  # 6 verde
]
OUTROS = "#6b6a63"  # cauda longa: cinza neutro, nunca um 7º hue gerado

# ── status (reservado: só polaridade de variação, sempre com sinal no rótulo) ──
ALTA = "#d03b3b"    # custo subiu
BAIXA = "#0ca30c"   # custo caiu

TEMPLATE = "locates_dark"


def registrar_template() -> None:
    pio.templates[TEMPLATE] = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family='"Poppins", system-ui, -apple-system, "Segoe UI", sans-serif',
                size=13,
                color=TINTA_2,
            ),
            title=dict(font=dict(size=16, color=TINTA), x=0, xanchor="left"),
            colorway=SERIES,
            xaxis=dict(
                showgrid=False,
                linecolor=BASE,
                zeroline=False,
                tickfont=dict(color=TINTA_MUDA, size=12),
                title=dict(font=dict(color=TINTA_MUDA, size=12)),
            ),
            yaxis=dict(
                gridcolor=GRADE,
                griddash="solid",
                gridwidth=1,
                linecolor="rgba(0,0,0,0)",
                zerolinecolor=BASE,
                tickfont=dict(color=TINTA_MUDA, size=12),
                title=dict(font=dict(color=TINTA_MUDA, size=12)),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                x=0,
                font=dict(color=TINTA_2, size=12),
                bgcolor="rgba(0,0,0,0)",
            ),
            hoverlabel=dict(
                bgcolor="#1f1f27",
                bordercolor=BASE,
                font=dict(color=TINTA, size=13),
            ),
            margin=dict(l=8, r=8, t=48, b=8),
            separators=",.",  # decimal vírgula, milhar ponto
        )
    )


def mapa_cores(entidades: list[str]) -> dict[str, str]:
    """Fixa cor por entidade na ordem dada; do 7º em diante, cinza de 'Outros'."""
    cores = {e: SERIES[i] if i < len(SERIES) else OUTROS for i, e in enumerate(entidades)}
    cores["Outros"] = OUTROS
    return cores


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

.stApp {{
    background:
        radial-gradient(circle at 0% 0%, rgba(80, 64, 136, 0.20) 0%, {PLANO} 34%),
        linear-gradient(180deg, {PLANO} 0%, #121218 100%);
    color: {TINTA};
    font-family: 'Poppins', system-ui, -apple-system, sans-serif;
}}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }}

h1, h2, h3, h4 {{ font-family: 'Poppins', system-ui, sans-serif; color: {TINTA}; }}

.cabecalho {{
    border: 1px solid rgba(53, 208, 126, 0.22);
    border-radius: 18px;
    padding: 1.2rem 1.5rem;
    background: linear-gradient(125deg, rgba(80, 64, 136, 0.30), rgba(13, 13, 16, 0.45));
    margin-bottom: 1.4rem;
}}
.cabecalho h1 {{ font-size: 1.75rem; font-weight: 700; margin: 0; letter-spacing: -0.01em; }}
.cabecalho p  {{ margin: 0.45rem 0 0; color: #DACDFF; font-size: 0.94rem; }}

.tile {{
    background: rgba(255, 255, 255, 0.028);
    border: 1px solid rgba(255, 255, 255, 0.085);
    border-radius: 14px;
    padding: 0.95rem 1.05rem;
    height: 100%;
}}
.tile .rotulo {{
    color: {TINTA_MUDA}; font-size: 0.78rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 0.35rem;
}}
.tile .valor {{ color: {TINTA}; font-size: 1.72rem; font-weight: 600; line-height: 1.1; margin: 0; }}
.tile .nota  {{ color: {TINTA_2}; font-size: 0.82rem; margin: 0.4rem 0 0; }}
.tile .delta-alta  {{ color: {ALTA};  font-weight: 600; }}
.tile .delta-baixa {{ color: {BAIXA}; font-weight: 600; }}

.secao {{
    font-size: 1.05rem; font-weight: 600; color: {TINTA};
    margin: 2.0rem 0 0.2rem; padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}}
.legenda {{ color: {TINTA_MUDA}; font-size: 0.84rem; margin: 0.35rem 0 0.9rem; }}

div[data-testid="stMetricValue"] {{ color: {TINTA}; }}
</style>
"""
