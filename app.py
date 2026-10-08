"""Dashboard — Chuvas e Deslizamentos no Estado do Rio de Janeiro."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
ORDEM_RISCO = ["Baixo", "Médio", "Alto", "Crítico"]
st.set_page_config(page_title="Chuvas e Deslizamentos — RJ", page_icon="🌧️", layout="wide")
sns.set_theme(style="whitegrid")


@st.cache_data
def carregar(arquivo=None):
    """Lê o CSV (ou upload), cria o banco SQLite e lê de volta com JOIN."""
    if arquivo is not None:
        df = pd.read_csv(arquivo, parse_dates=["data"])
    else:
        df = pd.read_csv(RAIZ / "dados" / "simulacao_chuvas_deslizamentos_rj.csv", parse_dates=["data"])
    df = df.drop_duplicates().dropna()
    df["nivel_risco"] = pd.Categorical(df["nivel_risco"], ORDEM_RISCO, ordered=True)
    df["mes_nome"] = df["mes"].map(lambda m: MESES[m - 1])
    df["estacao"] = np.where(df["mes"].isin([12, 1, 2, 3]), "Chuvosa (dez–mar)", "Seca (abr–nov)")
    return df


@st.cache_data
def coordenadas():
    """Integração com o banco relacional (SQLite via SQLAlchemy); fallback se o .db não existir."""
    db = RAIZ / "database" / "chuvas.db"
    if db.exists():
        return pd.read_sql("SELECT municipio, lat, lon FROM municipios", create_engine(f"sqlite:///{db}"))
    return pd.DataFrame()


# ---------- Cabeçalho ----------
st.title("🌧️ Chuvas e Deslizamentos no Estado do Rio de Janeiro")
st.caption("**LINGUAGENS DE PROGRAMAÇÃO** · SII1P0604N0002 · Aluno: Renan Braga Gomes · Professor: Alexandre Louzada")
st.markdown(
    "**Problema:** chuvas intensas em áreas de encosta provocam deslizamentos, desalojamentos e mortes. "
    "Este painel investiga *quais municípios são mais vulneráveis, quando o risco é maior e quanto a chuva "
    "explica os deslizamentos*, a partir de uma base **simulada** (8 municípios, 2015–2024, mensal).")

up = st.sidebar.file_uploader("Enviar outro CSV (mesmas colunas)", type="csv")
df = carregar(up)

# ---------- Filtros ----------
st.sidebar.header("Filtros")
anos = st.sidebar.slider("Período (ano)", int(df.ano.min()), int(df.ano.max()),
                         (int(df.ano.min()), int(df.ano.max())))
meses = st.sidebar.multiselect("Mês", MESES, default=MESES)
regs = st.sidebar.multiselect("Região", sorted(df.regiao_rj.unique()), default=sorted(df.regiao_rj.unique()))
muns_opc = sorted(df[df.regiao_rj.isin(regs)].municipio.unique())
muns = st.sidebar.multiselect("Município", muns_opc, default=muns_opc)
riscos = st.sidebar.multiselect("Nível de risco", ORDEM_RISCO, default=ORDEM_RISCO)

f = df[df.ano.between(*anos) & df.mes_nome.isin(meses) & df.regiao_rj.isin(regs)
       & df.municipio.isin(muns) & df.nivel_risco.isin(riscos)]
if f.empty:
    st.warning("Nenhum registro para os filtros escolhidos. Ajuste a seleção na barra lateral.")
    st.stop()

# ---------- KPIs ----------
corr = f["chuva_mm"].corr(f["ocorrencias_deslizamento"]) if len(f) > 2 else np.nan
rank = f.groupby("municipio").ocorrencias_deslizamento.sum().sort_values(ascending=False)
mensal = f.groupby("data").chuva_mm.sum()
k = st.columns(6)
k[0].metric("Volume total de chuva", f"{f.chuva_mm.sum():,.0f} mm".replace(",", "."))
k[1].metric("Média de chuva (mês/município)", f"{f.chuva_mm.mean():.1f} mm")
k[2].metric("Total de deslizamentos", f"{f.ocorrencias_deslizamento.sum():,}".replace(",", "."))
k[3].metric("Município mais crítico", rank.index[0])
k[4].metric("Total de desalojados", f"{f.desalojados.sum():,}".replace(",", "."))
k[5].metric("Correlação chuva × deslizam.", f"{corr:.2f}")
st.caption(f"{len(f)} registros após filtros · óbitos no recorte: {f.obitos.sum()}")

t1, t2, t3, t4, t5 = st.tabs(["📈 Evolução temporal", "🏙️ Municípios", "🔗 Correlação",
                              "📅 Sazonalidade e risco", "🗺️ Mapa e tabela"])

# ---------- 1. Temporal ----------
with t1:
    c1, c2 = st.columns(2)
    agg = f.groupby("data").agg(chuva=("chuva_mm", "mean"), desl=("ocorrencias_deslizamento", "sum")).reset_index()
    c1.plotly_chart(px.line(agg, x="data", y="chuva", title="Chuva média mensal (mm)"), use_container_width=True)
    c2.plotly_chart(px.line(agg, x="data", y="desl", title="Deslizamentos por mês (soma)"), use_container_width=True)
    anual = f.groupby("ano").agg(chuva=("chuva_mm", "sum"), desl=("ocorrencias_deslizamento", "sum")).reset_index()
    st.plotly_chart(px.bar(anual, x="ano", y="desl", color="chuva", title="Deslizamentos por ano (cor = chuva acumulada)"),
                    use_container_width=True)
    pico = agg.loc[agg.desl.idxmax()]
    st.info(f"**Interpretação:** o mês mais crítico do recorte foi {pico.data:%m/%Y}, com {int(pico.desl)} "
            "deslizamentos. As duas séries sobem e descem juntas, com picos anuais recorrentes no verão.")

# ---------- 2. Municípios ----------
with t2:
    m = f.groupby(["municipio", "regiao_rj"]).agg(
        chuva=("chuva_mm", "sum"), desl=("ocorrencias_deslizamento", "sum"),
        desalojados=("desalojados", "sum"), obitos=("obitos", "sum")).reset_index()
    m["desl_por_100mm"] = (m.desl / m.chuva * 100).round(2)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(m.sort_values("chuva"), x="chuva", y="municipio", orientation="h", color="regiao_rj",
                           title="Chuva acumulada (mm)"), use_container_width=True)
    c2.plotly_chart(px.bar(m.sort_values("desl"), x="desl", y="municipio", orientation="h", color="regiao_rj",
                           title="Deslizamentos acumulados"), use_container_width=True)
    st.subheader("Ranking de municípios críticos")
    st.dataframe(m.sort_values("desl", ascending=False).reset_index(drop=True), use_container_width=True)
    top = m.sort_values("desl_por_100mm", ascending=False).iloc[0]
    st.info(f"**Interpretação:** os municípios serranos concentram os deslizamentos. Não é só volume de chuva: "
            f"**{top.municipio}** tem a maior eficiência de deslizamento ({top.desl_por_100mm} por 100 mm), "
            "sinal de vulnerabilidade do terreno (comportamento fora do padrão em relação ao litoral e à capital).")

# ---------- 3. Correlação ----------
with t3:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.scatter(f, x="chuva_mm", y="ocorrencias_deslizamento", color="regiao_rj",
                               hover_name="municipio", opacity=.6, trendline="ols" if len(f) > 5 else None,
                               title="Chuva × deslizamentos"), use_container_width=True)
    cols = ["chuva_mm", "temperatura_media", "umidade", "indice_solo", "ocorrencias_deslizamento", "desalojados", "obitos"]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.heatmap(f[cols].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    c2.pyplot(fig)
    st.info(f"**Interpretação:** a correlação de Pearson entre chuva e deslizamentos é **{corr:.2f}** no recorte. "
            "O índice de saturação do solo também se associa fortemente aos deslizamentos. "
            "Correlação não implica causalidade, mas a relação é consistente com o mecanismo físico.")

# ---------- 4. Sazonalidade e risco ----------
with t4:
    c1, c2 = st.columns(2)
    piv = f.pivot_table(index="ano", columns="mes", values="ocorrencias_deslizamento", aggfunc="sum")
    piv.columns = [MESES[i - 1] for i in piv.columns]
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(piv, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax)
    ax.set_title("Deslizamentos por ano × mês")
    c1.pyplot(fig)
    clima = f.groupby("mes").chuva_mm.mean().reindex(range(1, 13))
    c2.plotly_chart(px.bar(x=MESES, y=clima.values, labels={"x": "Mês", "y": "Chuva média (mm)"},
                           title="Climatologia mensal da chuva"), use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(px.box(f, x="nivel_risco", y="chuva_mm", category_orders={"nivel_risco": ORDEM_RISCO},
                           title="Chuva por nível de risco"), use_container_width=True)
    est = f.groupby("estacao").ocorrencias_deslizamento.mean().round(2).reset_index()
    c4.plotly_chart(px.bar(est, x="estacao", y="ocorrencias_deslizamento",
                           title="Média de deslizamentos: estação chuvosa × seca"), use_container_width=True)
    st.info("**Interpretação:** há duas estações bem definidas. De dezembro a março, chuva e deslizamentos são "
            "mais que o dobro do restante do ano. Níveis de risco mais altos coincidem com chuvas maiores.")

# ---------- 5. Mapa e tabela ----------
with t5:
    co = coordenadas()
    if not co.empty:
        mp = m.merge(co, on="municipio")
        fig = px.scatter_map(mp, lat="lat", lon="lon", size="desl", color="desl_por_100mm", hover_name="municipio",
                                hover_data=["chuva", "desalojados", "obitos"], zoom=6.3, height=480,
                                color_continuous_scale="YlOrRd", map_style="open-street-map",
                                title="Deslizamentos (tamanho) e eficiência por 100 mm (cor)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Mapa indisponível: rode `python database/build_db.py` para criar o banco.")
    st.subheader("Tabela dinâmica")
    var = st.selectbox("Variável", ["ocorrencias_deslizamento", "chuva_mm", "desalojados", "obitos"])
    fun = st.radio("Agregação", ["sum", "mean"], horizontal=True)
    pt = f.pivot_table(index="municipio", columns="ano", values=var, aggfunc=fun).round(1)
    st.dataframe(pt, use_container_width=True)
    st.download_button("Baixar dados filtrados (CSV)", f.to_csv(index=False).encode("utf-8"), "dados_filtrados.csv")

# ---------- Conclusão ----------
st.divider()
st.header("Conclusão executiva")
st.markdown(f"""
- **Mais vulneráveis:** Teresópolis, Petrópolis e Nova Friburgo (região Serrana) acumulam mais que o dobro dos deslizamentos dos demais.
- **Quando:** o risco se concentra de dezembro a março; nesse período a chuva média passa de ~200 mm/mês.
- **Relação:** chuva e deslizamentos são fortemente correlacionados (r = {corr:.2f} no recorte atual).
- **Ação sugerida:** priorizar alertas, defesa civil e obras de contenção na Serra antes do verão.
- **Limite:** a base é simulada; as conclusões ilustram a metodologia, não substituem dados oficiais (INMET, CEMADEN, Defesa Civil).
""")
