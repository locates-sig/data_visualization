"""Painel de acompanhamento de custos AWS — dados do lake da Nekt.

Rode com:  streamlit run app.py
Requer `NEKT_MCP_TOKEN` no ambiente.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import dados
import formatos as f
import graficos as g
import tema as t
from nekt_client import NektClient, NektError

st.set_page_config(
    page_title="Locates | Custos AWS",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)
t.registrar_template()
st.markdown(t.CSS, unsafe_allow_html=True)


# ── dados ─────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _cliente() -> NektClient:
    return NektClient().connect()


@st.cache_data(ttl=1800, show_spinner="Consultando o lake da Nekt…")
def _carregar() -> dict[str, pd.DataFrame]:
    return dados.carregar(_cliente())


try:
    base = _carregar()
except NektError as erro:
    st.error(f"Não consegui ler os custos na Nekt.\n\n**{erro}**")
    st.info(
        "O painel lê `nekt_raw.aws_cost_explorer_*` pelo MCP da Nekt. "
        "Confira se `NEKT_MCP_TOKEN` está exportado no shell que subiu o Streamlit "
        "(`source ~/.config/locates/secrets.env`)."
    )
    st.stop()

total, servico, conta = base["total"], base["servico"], base["conta"]

inicio_util = dados.primeiro_dia_com_custo(total)
dia_parcial = total["dia"].max()
dia_fechado = dados.ultimo_dia_fechado(total)
sync = dados.instante_sync(total)

# Só entram meses cujos dias estão todos consolidados.
dias_por_mes = (
    total[total["dia"] <= dia_fechado].groupby("mes")["dia"].nunique().rename("dias")
)
meses_completos = [
    m for m, n in dias_por_mes.items() if n == m.days_in_month and m >= inicio_util.to_period("M").to_timestamp()
]
mes_ref = meses_completos[-1] if meses_completos else None
mes_ant = meses_completos[-2] if len(meses_completos) > 1 else None


# ── cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="cabecalho">
      <h1>Custos AWS</h1>
      <p>Conta 860134658538 · custo não-combinado (UnblendedCost) em USD, granularidade diária ·
         histórico de {f.dia_br(inicio_util)} a {f.dia_br(dia_parcial)} ·
         última sincronização da Nekt em {sync.strftime('%d/%m/%Y às %H:%M') if sync else '—'}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── filtros (uma linha, acima de tudo) ────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2.2, 2.2, 1.2])
with col_f1:
    janela = st.radio(
        "Janela das análises diárias",
        ["Últimos 30 dias", "Últimos 90 dias", "Mês em curso", "Todo o histórico"],
        horizontal=True,
        index=1,
    )
with col_f2:
    if mes_ref is not None and mes_ant is not None:
        opcoes = [f.mes_curto(m) for m in meses_completos]
        escolha = st.select_slider(
            "Comparação mês a mês",
            options=opcoes,
            value=(f.mes_curto(mes_ant), f.mes_curto(mes_ref)),
        )
        mapa_mes = dict(zip(opcoes, meses_completos))
        mes_base_sel, mes_ref_sel = mapa_mes[escolha[0]], mapa_mes[escolha[1]]
    else:
        mes_base_sel = mes_ref_sel = None
with col_f3:
    st.write("")
    if st.button("Recarregar dados", width="stretch"):
        _carregar.clear()
        st.rerun()

if janela == "Últimos 30 dias":
    ini_janela = dia_parcial - pd.Timedelta(days=29)
elif janela == "Últimos 90 dias":
    ini_janela = dia_parcial - pd.Timedelta(days=89)
elif janela == "Mês em curso":
    ini_janela = dia_parcial.to_period("M").to_timestamp()
else:
    ini_janela = inicio_util
ini_janela = max(ini_janela, inicio_util)


# ── indicadores ───────────────────────────────────────────────────────────────
proj = dados.projecao_mes(total, dia_parcial, dia_fechado)
soma_30d, ini_30d = dados.soma_ultimos_dias(total, dia_fechado, 30)
media_7d = total[(total["dia"] > dia_fechado - pd.Timedelta(days=7)) &
                 (total["dia"] <= dia_fechado)]["custo"].mean()
media_30d = total[(total["dia"] > dia_fechado - pd.Timedelta(days=30)) &
                  (total["dia"] <= dia_fechado)]["custo"].mean()

custo_ref = total[total["mes"] == mes_ref]["custo"].sum() if mes_ref is not None else 0.0
custo_ant = total[total["mes"] == mes_ant]["custo"].sum() if mes_ant is not None else 0.0
var_mes = (custo_ref - custo_ant) / custo_ant if custo_ant else float("nan")
var_7_30 = (media_7d - media_30d) / media_30d if media_30d else float("nan")
acumulado = total[total["dia"] >= inicio_util]["custo"].sum()


def tile(rotulo: str, valor: str, nota: str = "", delta: float | None = None) -> str:
    marca = ""
    if delta is not None and delta == delta:
        classe = "delta-alta" if delta > 0 else "delta-baixa"
        seta = "▲" if delta > 0 else "▼"
        marca = f'<span class="{classe}">{seta} {f.pct(delta)}</span> '
    return (
        f'<div class="tile"><p class="rotulo">{rotulo}</p>'
        f'<p class="valor">{valor}</p>'
        f'<p class="nota">{marca}{nota}</p></div>'
    )


nota_mes = f"{proj['dias_fechados']} de {proj['dias_no_mes']} dias fechados"
if proj["projecao"]:
    nota_mes += f" · projeção {f.usd(proj['projecao'], 0)}"
else:
    nota_mes += " · cedo demais para projetar"

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    tile("Últimos 30 dias", f.usd(soma_30d, 0),
         f"{f.dia_br(ini_30d)} a {f.dia_br(dia_fechado)}"),
    unsafe_allow_html=True,
)
c2.markdown(
    tile(f"{f.mes_curto(proj['mes'])} até agora", f.usd(proj["acumulado"], 0), nota_mes),
    unsafe_allow_html=True,
)
c3.markdown(
    tile(f"{f.mes_curto(mes_ref)} fechado" if mes_ref is not None else "Último mês fechado",
         f.usd(custo_ref, 0),
         f"contra {f.mes_curto(mes_ant)}" if mes_ant is not None else "sem mês anterior",
         var_mes),
    unsafe_allow_html=True,
)
c4.markdown(
    tile("Média diária (7 dias)", f.usd(media_7d),
         "contra a média de 30 dias", var_7_30),
    unsafe_allow_html=True,
)
c5.markdown(
    tile("Acumulado no histórico", f.usd(acumulado, 0),
         f"desde {f.dia_br(inicio_util)}"),
    unsafe_allow_html=True,
)


# ── série diária ──────────────────────────────────────────────────────────────
st.markdown('<div class="secao">Custo diário</div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="legenda">Janela: {janela.lower()}. A barra translúcida é o dia ainda aberto '
    f'({f.dia_br(dia_parcial)}) — a AWS só o fecha depois, então ele sempre parece baixo e fica '
    'fora de médias, projeções e comparações.</p>',
    unsafe_allow_html=True,
)
serie = dados.serie_diaria(total, ini_janela, dia_parcial)
st.plotly_chart(g.serie_diaria(serie, dia_parcial), width="stretch")


# ── visão mensal ──────────────────────────────────────────────────────────────
st.markdown('<div class="secao">Fatura por mês</div>', unsafe_allow_html=True)
col_a, col_b = st.columns([1, 1])
mensal = dados.serie_mensal(total[total["dia"] >= inicio_util], dia_parcial)
ordem_meses = list(mensal["rotulo"])
with col_a:
    st.markdown('<p class="legenda">Total mensal consolidado.</p>', unsafe_allow_html=True)
    st.plotly_chart(g.barras_mensais(mensal, proj), width="stretch")

historico = servico[servico["dia"] >= inicio_util]
ranking_global = historico.groupby("servico")["custo"].sum().sort_values(ascending=False)
ordem_cores = list(ranking_global.index[:6])
cores = t.mapa_cores(ordem_cores)
ordem_pilha = ordem_cores + ["Outros"]

# A composição só é comparável entre meses inteiros — o mês em curso viraria uma
# coluna raquítica ao lado das outras e sugeriria uma queda que não existe.
evolucao = dados.evolucao_por_servico(
    historico[historico["mes"].isin(meses_completos)], top_n=6
)
meses_pilha = [f.mes_curto(m) for m in meses_completos]
with col_b:
    st.markdown(
        '<p class="legenda">Composição dos meses fechados: os 6 maiores serviços do '
        'histórico, o resto somado em Outros.</p>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        g.empilhado_mensal(evolucao, cores, ordem_pilha, meses_pilha), width="stretch"
    )


# ── serviços ──────────────────────────────────────────────────────────────────
st.markdown('<div class="secao">Onde o dinheiro vai</div>', unsafe_allow_html=True)
col_c, col_d = st.columns([1, 1])
comp = dados.por_servico(servico, ini_janela, dia_parcial)
comp_visivel = comp[comp["custo"].abs() > 0.005]
with col_c:
    st.markdown(
        f'<p class="legenda">Custo por serviço na janela selecionada '
        f'({f.dia_br(ini_janela)} a {f.dia_br(dia_parcial)}). '
        'Serviços com custo zero ficam de fora.</p>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(g.composicao_servicos(comp_visivel, cores), width="stretch")

with col_d:
    if mes_ref_sel is not None and mes_base_sel is not None and mes_ref_sel != mes_base_sel:
        st.markdown(
            f'<p class="legenda">O que mudou entre {f.mes_curto(mes_base_sel)} e '
            f'{f.mes_curto(mes_ref_sel)}, serviço a serviço — a soma destas barras é a '
            'variação da fatura.</p>',
            unsafe_allow_html=True,
        )
        var = dados.variacao_entre_meses(servico, mes_ref_sel, mes_base_sel)
        var_visivel = var[var["delta"].abs() > 0.005]
        st.plotly_chart(
            g.deltas_servicos(var_visivel, f.mes_curto(mes_ref_sel), f.mes_curto(mes_base_sel)),
            width="stretch",
        )
    else:
        st.info("Escolha dois meses diferentes no comparador acima para ver a variação.")


# ── contas vinculadas ─────────────────────────────────────────────────────────
contas_com_custo = conta.groupby("conta")["custo"].sum()
contas_ativas = contas_com_custo[contas_com_custo.abs() > 0.005]
if len(contas_ativas) > 1:
    st.markdown('<div class="secao">Contas vinculadas</div>', unsafe_allow_html=True)
    cores_conta = t.mapa_cores(list(contas_ativas.sort_values(ascending=False).index))
    recorte = conta[(conta["dia"] >= inicio_util) &
                    (conta["conta"].isin(contas_ativas.index))].copy()
    recorte["rotulo"] = recorte["mes"].map(f.mes_curto)
    st.plotly_chart(g.series_por_conta(recorte, cores_conta, ordem_meses), width="stretch")
else:
    zeradas = [c for c in contas_com_custo.index if c not in contas_ativas.index]
    if zeradas:
        st.caption(
            f"Toda a fatura está na conta {contas_ativas.index[0]}. "
            f"Conta{'s' if len(zeradas) > 1 else ''} vinculada{'s' if len(zeradas) > 1 else ''} "
            f"{', '.join(zeradas)} sem custo no período."
        )


# ── dados e procedência ───────────────────────────────────────────────────────
st.markdown('<div class="secao">Dados e procedência</div>', unsafe_allow_html=True)
aba_tab, aba_proc = st.tabs(["Tabela", "De onde vem e o que observar"])

with aba_tab:
    detalhe = (
        servico[(servico["dia"] >= ini_janela) & (servico["dia"] <= dia_parcial)]
        .pivot_table(index="dia", columns="servico", values="custo", aggfunc="sum")
        .fillna(0.0)
    )
    detalhe = detalhe.loc[:, detalhe.abs().sum().sort_values(ascending=False).index]
    detalhe.insert(0, "Total do dia", detalhe.sum(axis=1))
    detalhe.index = detalhe.index.strftime("%d/%m/%Y")
    st.dataframe(detalhe.style.format("{:,.2f}"), width="stretch", height=420)
    st.download_button(
        "Baixar CSV da janela",
        detalhe.to_csv().encode("utf-8"),
        file_name=f"custos_aws_{ini_janela:%Y%m%d}_{dia_parcial:%Y%m%d}.csv",
        mime="text/csv",
    )

with aba_proc:
    st.markdown(
        f"""
**Fonte.** Source `{dados.SOURCE_SLUG}` (conector AWS Cost Explorer) na camada Raw do lake
da Nekt, lida por SQL no Athena. Três streams incrementais, chave
`(time_period_start, group_by_value, metric_name)` — por isso não há dupla contagem mesmo
com vários syncs no mesmo mês:

- `{dados.DB}.{dados.TB_TOTAL}` — total da conta por dia
- `{dados.DB}.{dados.TB_SERVICO}` — custo por serviço por dia
- `{dados.DB}.{dados.TB_CONTA}` — custo por conta vinculada por dia

Última sincronização: **{sync.strftime('%d/%m/%Y às %H:%M') if sync else '—'}**.
Os totais das três tabelas batem centavo a centavo no período inteiro.

**O que observar ao ler os números:**

- **O histórico só começa em {f.dia_br(inicio_util)}.** Os dias anteriores existem nas
  tabelas com custo zero — o conector trouxe a janela inteira que o Cost Explorer devolveu,
  não custo que sumiu. Tudo neste painel ignora esse trecho.
- **O último dia ({f.dia_br(dia_parcial)}) é parcial.** O sync roda por volta do meio-dia e
  pega o dia em curso pela metade. Ele aparece marcado nos gráficos e fica fora de médias,
  projeções e comparações.
- **A métrica é `UnblendedCost`**: o valor como a AWS cobra no dia, sem diluir compras
  antecipadas. Reserved Instances e Savings Plans aparecem inteiros no dia da cobrança — é o
  que explica picos isolados no primeiro dia do mês.
- **Valores negativos são créditos e estornos** (o caso recorrente aqui é `AWS Data Transfer`).
- **`Tax` é uma linha do próprio Cost Explorer**, não um serviço; ela entra no total.
- **Moeda: USD.** Não há taxa de câmbio na Nekt, então nada é convertido para real.
"""
    )

st.caption(
    f"Painel gerado em {dt.datetime.now():%d/%m/%Y às %H:%M} · dados em cache por 30 minutos · "
    "Locates"
)
