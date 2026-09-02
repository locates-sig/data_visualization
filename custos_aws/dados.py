"""Carga e tratamento dos dados de custo AWS que vivem no lake da Nekt.

Fonte: source `aws-cost-explorer-jfdJ` (conector AWS Cost Explorer), camada Raw.
Três streams, todos incrementais, granularidade diária, métrica `UnblendedCost` em USD:

    nekt_raw.aws_cost_explorer_cost_and_usage         total da conta por dia
    nekt_raw.aws_cost_explorer_cost_by_service        custo por serviço por dia
    nekt_raw.aws_cost_explorer_cost_by_linked_account custo por conta vinculada por dia

Os três volumes são pequenos (< 4k linhas somadas), então cada um é carregado inteiro
uma vez e todo o recorte acontece em pandas — os filtros do painel não voltam ao Athena.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from formatos import mes_curto as rotulo_mes
from nekt_client import NektClient

DB = "nekt_raw"
TB_TOTAL = "aws_cost_explorer_cost_and_usage"
TB_SERVICO = "aws_cost_explorer_cost_by_service"
TB_CONTA = "aws_cost_explorer_cost_by_linked_account"

SOURCE_SLUG = "aws-cost-explorer-jfdJ"

SQL_TOTAL = f"""
SELECT time_period_start AS dia,
       CAST(amount AS double) AS custo,
       unit AS moeda,
       CAST(_nekt_sync_at AS bigint) AS sync_at
FROM "{DB}"."{TB_TOTAL}"
WHERE metric_name = 'UnblendedCost'
ORDER BY 1
"""

SQL_SERVICO = f"""
SELECT time_period_start AS dia,
       group_by_value AS servico,
       CAST(amount AS double) AS custo,
       unit AS moeda,
       CAST(_nekt_sync_at AS bigint) AS sync_at
FROM "{DB}"."{TB_SERVICO}"
WHERE metric_name = 'UnblendedCost'
ORDER BY 1, 2
"""

SQL_CONTA = f"""
SELECT time_period_start AS dia,
       group_by_value AS conta,
       CAST(amount AS double) AS custo,
       unit AS moeda,
       CAST(_nekt_sync_at AS bigint) AS sync_at
FROM "{DB}"."{TB_CONTA}"
WHERE metric_name = 'UnblendedCost'
ORDER BY 1, 2
"""


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dia"] = pd.to_datetime(df["dia"])
    df["custo"] = pd.to_numeric(df["custo"], errors="coerce").fillna(0.0)
    df["sync_at"] = pd.to_numeric(df["sync_at"], errors="coerce")
    df["mes"] = df["dia"].dt.to_period("M").dt.to_timestamp()
    return df


def carregar(cliente: NektClient) -> dict[str, pd.DataFrame]:
    """Traz os três streams já tipados."""
    return {
        "total": _preparar(cliente.query(SQL_TOTAL)),
        "servico": _preparar(cliente.query(SQL_SERVICO)),
        "conta": _preparar(cliente.query(SQL_CONTA)),
    }


# ── janelas de validade ───────────────────────────────────────────────────────
LIMIAR_CUSTO = 1.0  # USD/dia — abaixo disso é ruído de arredondamento, não cobrança


def primeiro_dia_com_custo(total: pd.DataFrame) -> pd.Timestamp:
    """Início do histórico que serve para análise.

    O conector puxou a janela inteira que o Cost Explorer devolveu, mas os meses
    anteriores à cobrança efetiva vieram sem custo — não zero limpo, e sim resíduos da
    ordem de 1e-9 que fariam `custo > 0` disparar no primeiro dia da série. Daí o limiar:
    o histórico começa no primeiro dia que custou pelo menos um dólar.
    """
    com_custo = total.loc[total["custo"] >= LIMIAR_CUSTO, "dia"]
    return com_custo.min() if not com_custo.empty else total["dia"].min()


def ultimo_dia_fechado(total: pd.DataFrame) -> pd.Timestamp:
    """Último dia com custo consolidado.

    O Cost Explorer devolve o dia mais recente ainda em curso, sistematicamente
    subestimado (o sync do meio-dia só viu meia jornada). Ele entra nos gráficos marcado
    como parcial, mas nunca em média, projeção ou comparação.
    """
    return total["dia"].max() - pd.Timedelta(days=1)


def instante_sync(total: pd.DataFrame) -> dt.datetime | None:
    if total.empty or total["sync_at"].isna().all():
        return None
    return dt.datetime.fromtimestamp(int(total["sync_at"].max()))


# ── agregações ────────────────────────────────────────────────────────────────
def serie_diaria(total: pd.DataFrame, inicio, fim) -> pd.DataFrame:
    df = total[(total["dia"] >= inicio) & (total["dia"] <= fim)][["dia", "custo"]].copy()
    df = df.sort_values("dia").reset_index(drop=True)
    df["media_movel_7d"] = df["custo"].rolling(7, min_periods=3).mean()
    return df


def serie_mensal(total: pd.DataFrame, dia_parcial: pd.Timestamp) -> pd.DataFrame:
    """Custo por mês, sinalizando qual mês ainda está em curso.

    O mês em curso é o do último dia disponível — não o do último dia fechado, que no
    primeiro dia de um mês novo ainda apontaria para o mês anterior (já completo).
    """
    df = total.groupby("mes", as_index=False)["custo"].sum()
    mes_corrente = dia_parcial.to_period("M").to_timestamp()
    df["parcial"] = df["mes"] >= mes_corrente
    df["rotulo"] = df["mes"].map(rotulo_mes)
    return df.sort_values("mes").reset_index(drop=True)


def por_servico(servico: pd.DataFrame, inicio, fim) -> pd.DataFrame:
    df = servico[(servico["dia"] >= inicio) & (servico["dia"] <= fim)]
    agg = df.groupby("servico", as_index=False)["custo"].sum()
    agg = agg.sort_values("custo", ascending=False).reset_index(drop=True)
    total = agg["custo"].sum()
    agg["participacao"] = agg["custo"] / total if total else 0.0
    return agg


def evolucao_por_servico(servico: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    """Série mensal por serviço, com a cauda longa colapsada em 'Outros'."""
    mensal = servico.groupby(["mes", "servico"], as_index=False)["custo"].sum()
    ranking = (
        mensal.groupby("servico")["custo"].sum().sort_values(ascending=False).index[:top_n]
    )
    mensal["grupo"] = mensal["servico"].where(mensal["servico"].isin(ranking), "Outros")
    agg = mensal.groupby(["mes", "grupo"], as_index=False)["custo"].sum()
    agg["rotulo"] = agg["mes"].map(rotulo_mes)
    return agg


def variacao_entre_meses(
    servico: pd.DataFrame, mes_ref: pd.Timestamp, mes_base: pd.Timestamp
) -> pd.DataFrame:
    """Δ por serviço entre dois meses — o que explica a mudança na fatura."""
    ref = servico[servico["mes"] == mes_ref].groupby("servico")["custo"].sum()
    base = servico[servico["mes"] == mes_base].groupby("servico")["custo"].sum()
    df = pd.concat([base.rename("base"), ref.rename("ref")], axis=1).fillna(0.0)
    df["delta"] = df["ref"] - df["base"]
    df["delta_pct"] = df.apply(
        lambda r: (r["delta"] / r["base"]) if r["base"] else float("nan"), axis=1
    )
    return df.reset_index().sort_values("delta", key=abs, ascending=False)


def projecao_mes(
    total: pd.DataFrame, dia_parcial: pd.Timestamp, fechado_ate: pd.Timestamp
) -> dict:
    """Estado do mês em curso e seu fechamento estimado.

    O mês em curso é o do último dia disponível, e só os dias já consolidados dele
    alimentam a média. Num dia 1º ainda aberto não há dia fechado nenhum: aí a projeção
    sai como None em vez de virar um número inventado sobre zero observação.
    """
    mes = dia_parcial.to_period("M").to_timestamp()
    dias_mes = total[(total["mes"] == mes) & (total["dia"] <= fechado_ate)]
    n_dias = len(dias_mes)
    acumulado_fechado = dias_mes["custo"].sum()
    acumulado_total = total[total["mes"] == mes]["custo"].sum()  # inclui o dia parcial
    dias_no_mes = mes.days_in_month
    media = acumulado_fechado / n_dias if n_dias else None
    return {
        "mes": mes,
        "acumulado": acumulado_total,
        "acumulado_fechado": acumulado_fechado,
        "dias_fechados": n_dias,
        "dias_no_mes": dias_no_mes,
        "media_diaria": media,
        "projecao": media * dias_no_mes if media is not None else None,
    }


def soma_ultimos_dias(
    total: pd.DataFrame, fechado_ate: pd.Timestamp, janela: int = 30
) -> tuple[float, pd.Timestamp]:
    """Quanto custaram os últimos N dias corridos já consolidados.

    Preferido a uma extrapolação "média × 30": como as compras antecipadas caem inteiras
    no dia da cobrança (ver `UnblendedCost`), multiplicar uma média que não contém esse
    dia subestima o mês, e uma que contém superestima. A soma de uma janela fixa é o que
    de fato saiu no período, sem prometer ser um mês.
    """
    inicio = fechado_ate - pd.Timedelta(days=janela - 1)
    df = total[(total["dia"] >= inicio) & (total["dia"] <= fechado_ate)]
    return df["custo"].sum(), inicio
