"""Cria o banco SQLite (modelagem relacional) a partir do CSV.
Tabelas: municipios (dimensão) e registros (fato, FK -> municipios)."""
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent.parent
COORD = {"Rio de Janeiro": (-22.9068, -43.1729), "Niterói": (-22.8832, -43.1034),
         "Nova Iguaçu": (-22.7592, -43.4511), "Petrópolis": (-22.5050, -43.1786),
         "Teresópolis": (-22.4120, -42.9660), "Nova Friburgo": (-22.2819, -42.5311),
         "Angra dos Reis": (-23.0067, -44.3181), "Campos dos Goytacazes": (-21.7545, -41.3244)}

def main():
    df = pd.read_csv(RAIZ / "dados" / "simulacao_chuvas_deslizamentos_rj.csv", parse_dates=["data"])
    mun = df[["municipio", "regiao_rj"]].drop_duplicates().sort_values("municipio").reset_index(drop=True)
    mun["id_municipio"] = mun.index + 1
    mun["lat"] = mun.municipio.map(lambda m: COORD[m][0])
    mun["lon"] = mun.municipio.map(lambda m: COORD[m][1])
    reg = df.merge(mun[["municipio", "id_municipio"]], on="municipio").drop(columns=["municipio", "regiao_rj"])
    eng = create_engine(f"sqlite:///{RAIZ / 'database' / 'chuvas.db'}")
    mun.to_sql("municipios", eng, if_exists="replace", index=False)
    reg.to_sql("registros", eng, if_exists="replace", index=False)
    print(f"OK: {len(mun)} municípios, {len(reg)} registros")

if __name__ == "__main__":
    main()
