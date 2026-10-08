# 🌧️ Chuvas e Deslizamentos no Estado do Rio de Janeiro

Projeto G1 — Análise e Visualização de Dados com Python (Tema 02).

**Disciplina:** LINGUAGENS DE PROGRAMAÇÃO — SII1P0604N0002  
**Aluno:** Renan Braga Gomes  
**Professor:** Alexandre Louzada

- **Dashboard:** https://g1projetopratico.streamlit.app
- **Página do projeto:** https://SEU-USUARIO.github.io/projeto-chuvas-deslizamentos-rj/
- **Repositório:** [https://github.com/SEU-USUARIO/projeto-chuvas-deslizamentos-rj](https://github.com/Blenkzx/G1_Projeto_pratico)

## Problema
Investigar a relação entre chuva e deslizamentos em 8 municípios do RJ (base **simulada**, 2015–2024): municípios vulneráveis, períodos críticos, sazonalidade e correlação.

## Tecnologias
Python · Pandas · Matplotlib · Seaborn · Streamlit · GitHub · Plotly · SQLAlchemy + SQLite

## Funcionalidades
- **Intermediárias:** filtros múltiplos (ano, mês, região, município, risco), KPIs dinâmicos, análise temporal, dashboard em abas, comparação entre municípios, upload de CSV.
- **Avançadas:** persistência/modelagem relacional (SQLAlchemy + SQLite: tabelas `municipios` e `registros`), mapa interativo (Plotly) e correlação estatística (Pearson + matriz).

## Estrutura
```
app.py · requirements.txt · README.md · index.html
dados/      CSV original
database/   build_db.py + chuvas.db
notebooks/  analise_chuvas_deslizamentos.ipynb
imagens/    gráficos usados no index.html
```

## Como executar
```bash
pip install -r requirements.txt
python database/build_db.py      # opcional: recria o banco
streamlit run app.py
```

## Principais resultados
Serra (Teresópolis, Petrópolis, Nova Friburgo) concentra 57% dos deslizamentos; dezembro–março é o período crítico; correlação chuva × deslizamentos r ≈ 0,82.

## Limitações
Dados simulados (a população varia mês a mês no mesmo município e não há coordenadas na base original). Não substitui dados oficiais (INMET, CEMADEN, Defesa Civil).
