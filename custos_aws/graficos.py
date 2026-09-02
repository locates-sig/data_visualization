"""Figuras do painel.

Convenções aplicadas em todas: um eixo só (nunca dois y), marcas finas com ponta
arredondada de 4px ancorada na linha de base, gap de 2px entre segmentos empilhados,
grade discreta, legenda sempre presente quando há duas ou mais séries, rótulo direto
só onde ele cabe e informa, e hover em toda figura.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import formatos as f
import tema as t

ALTURA_PADRAO = 380


def _base(fig: go.Figure, altura: int = ALTURA_PADRAO, titulo: str | None = None,
          margem_esq: int = 68) -> go.Figure:
    fig.update_layout(
        template=t.TEMPLATE,
        height=altura,
        title=titulo,
        hovermode="x unified",
        margin=dict(l=margem_esq, r=24, t=52, b=44),
    )
    return fig


def _ticks_data(dias: pd.Series, alvo: int = 8) -> tuple[list, list]:
    """Ticks de data em pt-BR — o formato nativo do Plotly sai em inglês."""
    dias = list(pd.to_datetime(dias).drop_duplicates().sort_values())
    if not dias:
        return [], []
    passo = max(1, len(dias) // alvo)
    escolhidos = dias[::passo]
    if dias[-1] not in escolhidos:
        # o dia mais recente é o que o leitor procura primeiro; ele sempre ganha um tick
        if len(escolhidos) > 1 and (dias[-1] - escolhidos[-1]).days < passo * 0.6:
            escolhidos = escolhidos[:-1]
        escolhidos = escolhidos + [dias[-1]]
    return escolhidos, [f"{d.day:02d}/{f.MESES[d.month]}" for d in escolhidos]


def serie_diaria(df: pd.DataFrame, dia_parcial: pd.Timestamp) -> go.Figure:
    """Custo por dia + média móvel de 7 dias. O último dia entra marcado como parcial."""
    fechados = df[df["dia"] != dia_parcial]
    parcial = df[df["dia"] == dia_parcial]

    fig = go.Figure()
    fig.add_bar(
        x=fechados["dia"], y=fechados["custo"],
        name="Custo do dia",
        marker=dict(color=t.SERIES[0], cornerradius=4, line=dict(width=0)),
        hovertemplate="%{x|%d/%m/%Y}<br>Custo: US$ %{y:,.2f}<extra></extra>",
    )
    if not parcial.empty:
        fig.add_bar(
            x=parcial["dia"], y=parcial["custo"],
            name="Dia em curso (parcial)",
            marker=dict(
                color="rgba(57, 135, 229, 0.32)",
                cornerradius=4,
                line=dict(color=t.SERIES[0], width=1),
            ),
            hovertemplate="%{x|%d/%m/%Y} — dia ainda aberto<br>Parcial: US$ %{y:,.2f}<extra></extra>",
        )
    fig.add_scatter(
        x=df["dia"], y=df["media_movel_7d"],
        name="Média móvel 7 dias",
        mode="lines",
        line=dict(color=t.SERIES[1], width=2, shape="spline", smoothing=0.5),
        hovertemplate="Média 7d: US$ %{y:,.2f}<extra></extra>",
    )
    # Os picos do dia 1º são o imposto do mês lançado de uma vez; sem essa marca a
    # série parece ter outliers, e não um lançamento mensal previsível.
    primeiros = df[(df["dia"].dt.day == 1) & (df["custo"] > df["custo"].median() * 2)]
    for _, linha in primeiros.tail(3).iterrows():
        fig.add_annotation(
            x=linha["dia"], y=linha["custo"],
            text="imposto do mês",
            showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=t.TINTA_MUDA,
            ax=0, ay=-22,
            font=dict(color=t.TINTA_MUDA, size=11),
        )

    vals, txt = _ticks_data(df["dia"])
    borda = pd.Timedelta(days=2)
    fig.update_layout(barmode="overlay", bargap=0.25)
    fig.update_xaxes(tickvals=vals, ticktext=txt,
                     range=[df["dia"].min() - borda, df["dia"].max() + borda])
    fig.update_yaxes(title="US$ por dia", tickformat=",.0f", rangemode="tozero")
    return _base(fig, 400)


def barras_mensais(df: pd.DataFrame, projecao: dict | None = None) -> go.Figure:
    """Custo por mês. O mês em curso aparece translúcido, com a projeção marcada acima."""
    fechados = df[~df["parcial"]]
    corrente = df[df["parcial"]]
    ordem = list(df["rotulo"])

    fig = go.Figure()
    fig.add_bar(
        x=fechados["rotulo"], y=fechados["custo"],
        name="Mês fechado",
        marker=dict(color=t.SERIES[0], cornerradius=4, line=dict(width=0)),
        text=[f.usd(v, 0) for v in fechados["custo"]],
        textposition="outside",
        textfont=dict(color=t.TINTA_2, size=12),
        hovertemplate="%{x}<br>Custo: US$ %{y:,.2f}<extra></extra>",
    )
    if not corrente.empty:
        fig.add_bar(
            x=corrente["rotulo"], y=corrente["custo"],
            name="Mês em curso (parcial)",
            marker=dict(
                color="rgba(57, 135, 229, 0.30)",
                cornerradius=4,
                line=dict(color=t.SERIES[0], width=1),
            ),
            text=[f.usd(v, 0) for v in corrente["custo"]],
            textposition="outside",
            textfont=dict(color=t.TINTA_2, size=12),
            hovertemplate="%{x} — mês incompleto<br>Acumulado: US$ %{y:,.2f}<extra></extra>",
        )
        if projecao and projecao.get("projecao"):
            fig.add_scatter(
                x=[f.mes_curto(projecao["mes"])], y=[projecao["projecao"]],
                name="Projeção de fechamento",
                mode="markers+text",
                marker=dict(symbol="line-ew", size=30, line=dict(color=t.SERIES[3], width=3)),
                text=[f.usd(projecao["projecao"], 0)],
                textposition="top center",
                textfont=dict(color=t.SERIES[3], size=12),
                hovertemplate=(
                    "Projeção: US$ %{y:,.2f}<br>"
                    f"média de {projecao['dias_fechados']} dias fechados × "
                    f"{projecao['dias_no_mes']} dias<extra></extra>"
                ),
            )
    teto = max(float(df["custo"].max()), float(projecao["projecao"] or 0) if projecao else 0)
    fig.update_layout(barmode="overlay", bargap=0.55, hovermode="closest")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordem)
    fig.update_yaxes(title="US$ no mês", tickformat=",.0f", range=[0, teto * 1.14])
    return _base(fig, 400)


def composicao_servicos(df: pd.DataFrame, cores: dict[str, str], limite: int = 12) -> go.Figure:
    """Barras horizontais ordenadas por custo, com valor e participação direto na ponta."""
    d = df.head(limite).iloc[::-1]
    rotulos = [
        f"{f.usd(v)} · {f'{p * 100:.1f}'.replace('.', ',')}%"
        for v, p in zip(d["custo"], d["participacao"])
    ]

    fig = go.Figure()
    fig.add_bar(
        x=d["custo"], y=[f.nome_curto(s) for s in d["servico"]],
        orientation="h",
        marker=dict(
            color=[cores.get(s, t.OUTROS) for s in d["servico"]],
            cornerradius=4,
            line=dict(width=0),
        ),
        text=rotulos,
        textposition="outside",
        textfont=dict(color=t.TINTA_2, size=12),
        customdata=list(d["servico"]),
        hovertemplate="%{customdata}<br>Custo: US$ %{x:,.2f}<extra></extra>",
        showlegend=False,
    )
    folga = float(d["custo"].max()) * 1.62 if len(d) else 1.0
    fig.update_layout(bargap=0.35, hovermode="closest")
    fig.update_xaxes(title="US$ no período", tickformat=",.0f", showgrid=True,
                     gridcolor=t.GRADE, range=[0, folga])
    fig.update_yaxes(showgrid=False, automargin=True,
                     tickfont=dict(size=12, color=t.TINTA_2))
    altura = max(320, 34 * len(d) + 96)
    return _base(fig, altura, margem_esq=8)


def empilhado_mensal(df: pd.DataFrame, cores: dict[str, str], ordem: list[str],
                     ordem_meses: list[str]) -> go.Figure:
    """Composição mês a mês. Cor fixa por serviço — filtrar o período não repinta nada."""
    fig = go.Figure()
    for servico in ordem:
        d = df[df["grupo"] == servico]
        if d.empty:
            continue
        fig.add_bar(
            x=d["rotulo"], y=d["custo"],
            name=f.nome_curto(servico),
            marker=dict(
                color=cores.get(servico, t.OUTROS),
                line=dict(color=t.SUPERFICIE, width=2),  # gap de 2px entre segmentos
            ),
            hovertemplate="%{fullData.name}<br>%{x}: US$ %{y:,.2f}<extra></extra>",
        )
    fig.update_layout(barmode="stack", bargap=0.55, legend_traceorder="normal")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordem_meses)
    fig.update_yaxes(title="US$ no mês", tickformat=",.0f", rangemode="tozero")
    return _base(fig, 430)


def deltas_servicos(df: pd.DataFrame, rotulo_ref: str, rotulo_base: str,
                    limite: int = 10) -> go.Figure:
    """O que explica a diferença entre dois meses, serviço a serviço.

    Polaridade nunca é só cor: o rótulo carrega sinal (+/−) e a seta ▲/▼.
    """
    d = df.head(limite).iloc[::-1]
    cores = [t.ALTA if v > 0 else t.BAIXA for v in d["delta"]]
    setas = ["▲" if v > 0 else "▼" for v in d["delta"]]
    rotulos = [
        f"{s} {'+' if v > 0 else '−'}{f.usd(abs(v))[4:]}"
        for s, v in zip(setas, d["delta"])
    ]

    fig = go.Figure()
    fig.add_bar(
        x=d["delta"], y=[f.nome_curto(s) for s in d["servico"]],
        orientation="h",
        marker=dict(color=cores, cornerradius=4, line=dict(width=0)),
        text=rotulos,
        textposition="outside",
        textfont=dict(color=t.TINTA_2, size=12),
        customdata=d[["base", "ref"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>"
            + rotulo_base + ": US$ %{customdata[0]:,.2f}<br>"
            + rotulo_ref + ": US$ %{customdata[1]:,.2f}<br>"
            "Diferença: US$ %{x:,.2f}<extra></extra>"
        ),
        showlegend=False,
    )
    extremo = float(d["delta"].abs().max()) * 1.75 if len(d) else 1.0
    fig.update_layout(bargap=0.35, hovermode="closest")
    fig.update_xaxes(title=f"US$ — {rotulo_ref} menos {rotulo_base}", tickformat=",.0f",
                     showgrid=True, gridcolor=t.GRADE, zeroline=True, zerolinecolor=t.BASE,
                     zerolinewidth=1, range=[-extremo, extremo])
    fig.update_yaxes(showgrid=False, automargin=True,
                     tickfont=dict(size=12, color=t.TINTA_2))
    altura = max(320, 34 * len(d) + 96)
    return _base(fig, altura, margem_esq=8)


def series_por_conta(df: pd.DataFrame, cores: dict[str, str],
                     ordem_meses: list[str]) -> go.Figure:
    """Custo mensal por conta vinculada."""
    fig = go.Figure()
    for i, conta in enumerate(sorted(df["conta"].unique())):
        d = df[df["conta"] == conta].groupby("rotulo", as_index=False)["custo"].sum()
        fig.add_bar(
            x=d["rotulo"], y=d["custo"], name=conta,
            marker=dict(
                color=cores.get(conta, t.SERIES[i % len(t.SERIES)]),
                cornerradius=4,
                line=dict(color=t.SUPERFICIE, width=2),
            ),
            hovertemplate="Conta %{fullData.name}<br>%{x}: US$ %{y:,.2f}<extra></extra>",
        )
    fig.update_layout(barmode="group", bargap=0.42)
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordem_meses)
    fig.update_yaxes(title="US$ no mês", tickformat=",.0f", rangemode="tozero")
    return _base(fig, 340)
