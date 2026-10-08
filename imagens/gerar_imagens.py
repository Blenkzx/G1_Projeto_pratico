from pathlib import Path
import pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
R = Path(__file__).resolve().parent.parent
df = pd.read_csv(R/"dados"/"simulacao_chuvas_deslizamentos_rj.csv", parse_dates=["data"])
sns.set_theme(style="whitegrid")
def salvar(n): plt.tight_layout(); plt.savefig(R/"imagens"/n, dpi=110); plt.close()
m = df.groupby("data").agg(c=("chuva_mm","mean"), d=("ocorrencias_deslizamento","sum"))
fig, ax = plt.subplots(figsize=(9,4)); ax.plot(m.index, m.c, color="#2b6cb0"); ax.set_ylabel("Chuva média (mm)")
a2 = ax.twinx(); a2.plot(m.index, m.d, color="#c53030", alpha=.7); a2.set_ylabel("Deslizamentos"); a2.grid(False)
ax.set_title("Chuva (azul) e deslizamentos (vermelho) ao longo do tempo"); salvar("temporal.png")
r = df.groupby("municipio").ocorrencias_deslizamento.sum().sort_values()
plt.figure(figsize=(8,4)); sns.barplot(x=r.values, y=r.index, color="#dd6b20"); plt.title("Deslizamentos por município"); salvar("municipios.png")
plt.figure(figsize=(7,4.5)); sns.scatterplot(data=df, x="chuva_mm", y="ocorrencias_deslizamento", hue="regiao_rj", alpha=.6)
plt.title(f"Chuva × deslizamentos (r = {df.chuva_mm.corr(df.ocorrencias_deslizamento):.2f})"); salvar("dispersao.png")
p = df.pivot_table(index="ano", columns="mes", values="ocorrencias_deslizamento", aggfunc="sum")
plt.figure(figsize=(8,4.5)); sns.heatmap(p, annot=True, fmt=".0f", cmap="YlOrRd"); plt.title("Deslizamentos por ano × mês"); salvar("heatmap.png")
