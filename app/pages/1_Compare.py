import streamlit as st
import duckdb
import plotly.express as px

st.title("📈 Detailed Contract Comparison")
db_path = "data/processed/goldlens.duckdb"
conn = duckdb.connect(db_path)

df = conn.execute("SELECT trade_date, symbol, close_pg, volume, oi FROM prices_norm").fetchdf()
fig = px.line(df, x="trade_date", y="close_pg", color="symbol", title="Per-Gram Normalized Price History")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df.head(100))
conn.close()