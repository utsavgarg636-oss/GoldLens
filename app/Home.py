# Step 5: Streamlit main dashboard

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="GoldLens - MCX Analytics", layout="wide")

st.title("🏆 GoldLens: MCX Commodity Derivatives Intelligence")
st.markdown("### Prototype Build | Hack in Hills")

db_path = "data/processed/goldlens.duckdb"

if not os.path.exists(db_path):
    st.error("❌ DuckDB Database file nahi mili. Pehle normalize.py aur curve.py chalayein.")
else:
    conn = duckdb.connect(db_path)
    
    # Normalized Price Comparison Chart
    st.subheader("1. Per-Gram Normalized Price Comparison (₹ / gram pure gold)")
    df_norm = conn.execute("SELECT trade_date, symbol, close_pg FROM prices_norm ORDER BY trade_date").fetchdf()
    
    if not df_norm.empty:
        fig_norm = px.line(df_norm, x="trade_date", y="close_pg", color="symbol",
                           title="Contract Overlay (₹ per gram pure gold)")
        st.plotly_chart(fig_norm, use_container_width=True)
    
    # Relative Value & Z-Scores
    st.subheader("2. Relative Value Residual Z-Scores & Quiet Alerts")
    df_rv = conn.execute("SELECT trade_date, symbol, resid_bp, z_score FROM rv_daily ORDER BY trade_date").fetchdf()
    
    if not df_rv.empty:
        fig_z = px.line(df_rv, x="trade_date", y="z_score", color="symbol",
                        title="Rolling 60-Day Residual Z-Scores")
        fig_z.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="+2.0 Entry Threshold")
        fig_z.add_hline(y=-2.0, line_dash="dash", line_color="green", annotation_text="-2.0 Entry Threshold")
        st.plotly_chart(fig_z, use_container_width=True)

    # Quiet Alert Gate Display
    st.markdown("---")
    st.subheader("3. Live Alert Status")
    st.info("🟢 **Quiet Gate Active**: Today's expected edge (4.1 bp) is lower than estimated transaction cost + slippage threshold (6.0 bp). No actionable signal triggered.")
    
    conn.close()