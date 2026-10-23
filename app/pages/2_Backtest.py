import streamlit as st
import duckdb
import plotly.express as px

st.title("📊 Backtest & Performance Attribution")
db_path = "data/processed/goldlens.duckdb"
conn = duckdb.connect(db_path)

try:
    df_pnl = conn.execute("SELECT trade_date, pnl FROM pnl_daily").fetchdf()
    df_pnl["cum_pnl"] = df_pnl["pnl"].cumsum()
    fig = px.line(df_pnl, x="trade_date", y="cum_pnl", title="Cumulative Strategy Equity Curve (Net P&L)")
    st.plotly_chart(fig, use_container_width=True)
except Exception:
    st.info("Pehle `python -m src.goldlens.backtest` run karein.")

conn.close()