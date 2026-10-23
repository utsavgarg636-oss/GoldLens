import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.goldlens.relval import calculate_performance_metrics

st.set_page_config(page_title="GoldLens | Institutional Backtest Engine", page_icon="📊", layout="wide")

st.title("📊 Walk-Forward Backtest & Risk Performance Engine")
st.caption("Institutional Quantitative Performance Attribution with Zero Look-Ahead Bias (t+1 Fills)")

db_path = "data/processed/goldlens.duckdb"
conn = duckdb.connect(db_path)

try:
    df_pnl = conn.execute("SELECT trade_date, position, pnl FROM pnl_daily ORDER BY trade_date").fetchdf()
    
    if not df_pnl.empty:
        # Calculate Quantitative Performance Metrics
        metrics = calculate_performance_metrics(df_pnl["pnl"])
        
        # 1. Top Executive Metrics Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Sharpe Ratio (Annualized)", f"{metrics['sharpe_ratio']}")
        col2.metric("Sortino Ratio", f"{metrics['sortino_ratio']}")
        col3.metric("Max Drawdown", f"{metrics['max_drawdown_bp']} bp", delta="-Drawdown", delta_color="inverse")
        col4.metric("Win Rate", f"{metrics['win_rate_pct']}%")
        col5.metric("Profit Factor", f"{metrics['profit_factor']}")
        
        st.markdown("---")
        
        # 2. Cumulative Equity Curve
        df_pnl["cum_pnl_bp"] = df_pnl["pnl"].cumsum()
        
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=df_pnl["trade_date"], 
            y=df_pnl["cum_pnl_bp"], 
            mode="lines", 
            name="Strategy Net P&L (bp)",
            line=dict(color="#00E676", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(0, 230, 118, 0.1)"
        ))
        
        fig_equity.update_layout(
            template="plotly_dark",
            title="Cumulative Strategy Equity Curve (Basis Points Net Return)",
            height=420,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # 3. Monthly P&L Heatmap Breakdown
        st.subheader("🗓️ Monthly Performance Heatmap")
        
        df_pnl["trade_date"] = pd.to_datetime(df_pnl["trade_date"])
        df_pnl["year"] = df_pnl["trade_date"].dt.year
        df_pnl["month"] = df_pnl["trade_date"].dt.strftime("%b")
        
        monthly_pnl = df_pnl.groupby(["year", "month"])["pnl"].sum().reset_index()
        
        month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_pivot = monthly_pnl.pivot(index="year", columns="month", values="pnl").reindex(columns=month_order).fillna(0)
        
        fig_heatmap = px.imshow(
            monthly_pivot,
            labels=dict(x="Month", y="Year", color="P&L (bp)"),
            color_continuous_scale="RdYlGn",
            text_auto=".1f"
        )
        fig_heatmap.update_layout(template="plotly_dark", height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
    else:
        st.warning("No backtest data found. Run `python -m src.goldlens.backtest` first.")

except Exception as e:
    st.info("Run backtest pipeline to populate results: `python -m src.goldlens.backtest`")

conn.close()