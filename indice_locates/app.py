import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Locates | Índice de Projetos",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 0% 0%, rgba(100, 78, 166, 0.15) 0%, rgba(9, 9, 11, 1) 32%),
                    linear-gradient(180deg, #09090B 0%, #121218 100%);
        color: #F7F8FA;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero-card {
        border: 1px solid rgba(92, 243, 151, 0.25);
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
        background: linear-gradient(125deg, rgba(100, 78, 166, 0.28), rgba(9, 9, 11, 0.4));
        margin-bottom: 1.1rem;
    }
    .hero-title {
        font-size: 1.7rem;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF;
    }
    .hero-subtitle {
        margin: 0.4rem 0 0;
        color: #DACDFF;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 0.8rem;
    }
    .small-note {
        color: #B8B6C4;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_sample_data() -> pd.DataFrame:
    np.random.seed(42)
    months = pd.date_range("2024-01-01", periods=18, freq="MS")
    cities = ["Florianópolis", "São Paulo", "Curitiba", "Belo Horizonte"]
    categories = ["Residencial", "Comercial", "Misto"]

    records = []
    for month in months:
        for city in cities:
            for category in categories:
                vgv = np.random.uniform(15e6, 120e6)
                cost = vgv * np.random.uniform(0.55, 0.82)
                units = int(np.random.uniform(40, 320))
                area_m2 = np.random.uniform(3_000, 28_000)
                records.append(
                    {
                        "data_referencia": month,
                        "cidade": city,
                        "categoria": category,
                        "empreendimento": f"{category[:3].upper()}-{city[:3].upper()}-{month.strftime('%y%m')}",
                        "vgv": round(vgv, 2),
                        "custo": round(cost, 2),
                        "unidades": units,
                        "area_m2": round(area_m2, 2),
                    }
                )

    df = pd.DataFrame(records)
    df["margem"] = (df["vgv"] - df["custo"]) / df["vgv"]
    df["ticket_medio"] = df["vgv"] / df["unidades"]
    return df


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    expected = {
        "data_referencia",
        "cidade",
        "categoria",
        "empreendimento",
        "vgv",
        "custo",
        "unidades",
        "area_m2",
    }

    lower_map = {c.lower(): c for c in df.columns}
    if expected.issubset(set(lower_map.keys())):
        df = df.rename(columns={lower_map[col]: col for col in expected})
    else:
        missing = sorted(expected.difference(set(lower_map.keys())))
        raise ValueError(
            "Arquivo sem colunas obrigatórias. Faltando: " + ", ".join(missing)
        )

    df["data_referencia"] = pd.to_datetime(df["data_referencia"], errors="coerce")
    for col in ["vgv", "custo", "unidades", "area_m2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["data_referencia", "vgv", "custo", "unidades"])
    df["margem"] = (df["vgv"] - df["custo"]) / df["vgv"]
    df["ticket_medio"] = df["vgv"] / df["unidades"]
    return df


def fmt_currency(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.markdown(
    """
    <div class="hero-card">
        <p class="hero-title">Índice Locates • Analytics de Projetos</p>
        <p class="hero-subtitle">Acompanhe VGV, custo, margem e desempenho de empreendimentos com visão executiva.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Filtros")
    upload = st.file_uploader("Importar CSV", type=["csv"])

    if upload is None:
        st.caption("Sem arquivo: usando base de demonstração.")
        data = build_sample_data()
    else:
        try:
            uploaded_df = pd.read_csv(upload)
            data = normalize_input(uploaded_df)
            st.success("Arquivo carregado com sucesso.")
        except Exception as exc:
            st.error(f"Erro ao processar arquivo: {exc}")
            data = build_sample_data()
            st.caption("Aplicando base de demonstração como fallback.")

    min_date = data["data_referencia"].min().date()
    max_date = data["data_referencia"].max().date()
    date_range = st.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    city_options = sorted(data["cidade"].dropna().unique())
    selected_cities = st.multiselect("Cidade", city_options, default=city_options)

    category_options = sorted(data["categoria"].dropna().unique())
    selected_categories = st.multiselect(
        "Categoria", category_options, default=category_options
    )

if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start, end = pd.to_datetime(min_date), pd.to_datetime(max_date)

filtered = data[
    (data["data_referencia"].between(start, end))
    & (data["cidade"].isin(selected_cities))
    & (data["categoria"].isin(selected_categories))
].copy()

if filtered.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Empreendimentos", f"{filtered['empreendimento'].nunique()}")
with kpi2:
    st.metric("VGV Total", fmt_currency(filtered["vgv"].sum()))
with kpi3:
    st.metric("Margem Média", f"{filtered['margem'].mean() * 100:.1f}%")
with kpi4:
    st.metric("Ticket Médio", fmt_currency(filtered["ticket_medio"].mean()))

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    monthly = (
        filtered.assign(mes=filtered["data_referencia"].dt.to_period("M").dt.to_timestamp())
        .groupby("mes", as_index=False)["vgv"]
        .sum()
    )
    fig_monthly = px.area(
        monthly,
        x="mes",
        y="vgv",
        title="Evolução de VGV por mês",
        color_discrete_sequence=["#5CF397"],
    )
    fig_monthly.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F7F8FA",
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

with chart_col2:
    city_vgv = filtered.groupby("cidade", as_index=False)["vgv"].sum().sort_values("vgv")
    fig_city = px.bar(
        city_vgv,
        x="vgv",
        y="cidade",
        orientation="h",
        title="VGV por cidade",
        color="vgv",
        color_continuous_scale=["#644EA6", "#5CF397"],
    )
    fig_city.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F7F8FA",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_city, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    fig_scatter = px.scatter(
        filtered,
        x="custo",
        y="vgv",
        size="unidades",
        color="categoria",
        hover_name="empreendimento",
        title="Relação Custo x VGV",
        color_discrete_sequence=["#644EA6", "#5CF397", "#FFBC7D"],
    )
    fig_scatter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F7F8FA",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with chart_col4:
    margin_rank = (
        filtered.groupby("cidade", as_index=False)["margem"].mean().sort_values("margem")
    )
    fig_margin = px.bar(
        margin_rank,
        x="cidade",
        y="margem",
        title="Margem média por cidade",
        color="margem",
        color_continuous_scale=["#644EA6", "#5CF397"],
    )
    fig_margin.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F7F8FA",
        coloraxis_showscale=False,
        yaxis_tickformat=".0%",
    )
    st.plotly_chart(fig_margin, use_container_width=True)

best_city = (
    filtered.groupby("cidade", as_index=False)["margem"].mean().sort_values("margem", ascending=False).iloc[0]
)
worst_cost_ratio = (
    (filtered["custo"] / filtered["vgv"]).sort_values(ascending=False).iloc[0] * 100
)

st.markdown(
    f"""
    <div class="metric-card">
        <b>Insights rápidos</b><br>
        • Cidade com melhor margem média: <b>{best_city['cidade']}</b> ({best_city['margem'] * 100:.1f}%)<br>
        • Maior comprometimento de custo observado: <b>{worst_cost_ratio:.1f}%</b> do VGV
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Base filtrada")
show_cols = [
    "data_referencia",
    "cidade",
    "categoria",
    "empreendimento",
    "vgv",
    "custo",
    "margem",
    "unidades",
    "ticket_medio",
]

display_df = filtered[show_cols].sort_values("data_referencia", ascending=False)

st.dataframe(
    display_df,
    use_container_width=True,
    column_config={
        "data_referencia": st.column_config.DateColumn("Data"),
        "vgv": st.column_config.NumberColumn("VGV", format="R$ %.2f"),
        "custo": st.column_config.NumberColumn("Custo", format="R$ %.2f"),
        "margem": st.column_config.NumberColumn("Margem", format="%.2f"),
        "ticket_medio": st.column_config.NumberColumn("Ticket Médio", format="R$ %.2f"),
    },
)

csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Baixar dados filtrados (CSV)",
    data=csv,
    file_name="indice_locates_filtrado.csv",
    mime="text/csv",
)

st.markdown("<p class='small-note'>Dica: para usar sua base, inclua as colunas data_referencia, cidade, categoria, empreendimento, vgv, custo, unidades e area_m2.</p>", unsafe_allow_html=True)
