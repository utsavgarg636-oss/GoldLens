# GoldLens | Institutional Walk-Forward Backtest & Risk Performance Desk

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Guarantee project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.goldlens.db import get_backtest_pnl
from src.goldlens.relval import calculate_performance_metrics

st.set_page_config(
    page_title="GoldLens | Backtest & Risk Desk",
    page_icon="📊",
    layout="wide"
)

# Brand Header Logo (Renders directly above Home button in left taskbar)
logo_png = os.path.join(PROJECT_ROOT, "data", "goldlens_logo.png")
logo_svg = os.path.join(PROJECT_ROOT, "data", "goldlens_logo.svg")
logo_path = logo_png if os.path.exists(logo_png) else logo_svg
if os.path.exists(logo_path):
    st.logo(logo_path, size="large")

# Custom Bento & Glassmorphic CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
        height: 0px !important;
        border: none !important;
        z-index: 99999 !important;
    }
    [data-testid="stToolbar"] {
        display: flex !important;
        visibility: visible !important;
        position: fixed !important;
        top: 12px !important;
        left: 14px !important;
        z-index: 99999 !important;
        pointer-events: auto !important;
        width: auto !important;
        height: auto !important;
        background: transparent !important;
    }
    /* Completely hide unused decorations, menus, and the Cloud Deploy button */
    [data-testid="stDecoration"], 
    #MainMenu, 
    footer,
    [data-testid="stAppDeployButton"],
    .stAppDeployButton,
    .stDeployButton,
    button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0px !important;
        height: 0px !important;
    }

    /* Hide logo from top header when sidebar is collapsed (shows ONLY inside opened sidebar) */
    [data-testid="stHeaderLogo"],
    header[data-testid="stHeader"] [data-testid="stHeaderLogo"],
    header[data-testid="stHeader"] [data-testid="stLogo"],
    header[data-testid="stHeader"] img,
    [data-testid="stToolbar"] [data-testid="stHeaderLogo"],
    [data-testid="stToolbar"] [data-testid="stLogo"],
    [data-testid="stToolbar"] img {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0px !important;
        height: 0px !important;
    }
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[aria-label="Expand sidebar"] {
        display: flex !important;
        visibility: visible !important;
        pointer-events: auto !important;
        position: fixed !important;
        top: 12px !important;
        left: 14px !important;
        z-index: 9999999 !important;
        background: #FFFFFF !important;
        border: 2px solid #D97706 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 18px rgba(217, 119, 6, 0.28) !important;
        color: #D97706 !important;
        padding: 6px 12px !important;
        cursor: pointer !important;
    }
    [data-testid="stExpandSidebarButton"] svg, button[aria-label="Expand sidebar"] svg {
        fill: #D97706 !important;
        color: #D97706 !important;
    }
    [data-testid="stExpandSidebarButton"]:hover, button[aria-label="Expand sidebar"]:hover {
        background: #FEF3C7 !important;
        transform: scale(1.08) !important;
    }
    .stApp {
        background: radial-gradient(circle at 10% 20%, #F8FAFC 0%, #EDF2F7 90%);
        color: #0F172A;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    [data-testid="stAppViewContainer"] > section.main {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    .main .block-container, 
    [data-testid="stMainBlockContainer"], 
    .stMainBlockContainer, 
    div[data-testid="stMainBlockContainer"], 
    div.block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        margin-top: 0rem !important;
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(20px) saturate(190%);
        -webkit-backdrop-filter: blur(20px) saturate(190%);
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0.2rem !important;
    }
    [data-testid="stSidebarHeader"] {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 8px 12px 6px 12px !important;
        height: auto !important;
        min-height: 48px !important;
        margin-bottom: 2px !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.7) !important;
    }
    [data-testid="stSidebarLogo"],
    img.stLogo,
    img[data-testid="stSidebarLogo"],
    [data-testid="stLogo"] {
        height: 48px !important;
        max-height: 48px !important;
        width: auto !important;
        max-width: 220px !important;
        object-fit: contain !important;
        display: block !important;
        margin: 0 !important;
    }
    [data-testid="stLogoLink"] {
        display: flex !important;
        align-items: center !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebarCollapseButton"] button {
        background: #FFFFFF !important;
        border: 1px solid rgba(217, 119, 6, 0.35) !important;
        border-radius: 8px !important;
        color: #D97706 !important;
        padding: 4px 6px !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(217, 119, 6, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover {
        background: #FEF3C7 !important;
        transform: scale(1.05) !important;
    }
    [data-testid="stSidebarNav"] {
        padding-top: 4px !important;
        margin-top: 0rem !important;
    }
    [data-testid="stSidebarNavItems"] {
        padding-top: 0px !important;
        gap: 3px !important;
    }
    [data-testid="stSidebarNavLink"] {
        border-radius: 10px !important;
        padding: 8px 12px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        background: rgba(254, 243, 199, 0.5) !important;
        color: #B45309 !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: #FEF3C7 !important;
        color: #B45309 !important;
        font-weight: 700 !important;
        border-left: 3px solid #D97706 !important;
    }
    .bento-card {
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-top: 1.5px solid rgba(255, 255, 255, 1);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }
    .bento-label {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: #64748B;
    }
    .bento-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom: 16px;">
    <h1 style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin: 0;">
        📊 Institutional Walk-Forward <span style="background: linear-gradient(135deg, #D97706 0%, #B45309 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Backtest & Risk Desk</span>
    </h1>
    <div style="color: #64748B; font-size: 0.88rem; font-weight: 500; margin-top: 4px;">
        Quantitative performance attribution with strict t+1 execution fills (zero look-ahead bias)
    </div>
</div>
""", unsafe_allow_html=True)

df_pnl = get_backtest_pnl()

if not df_pnl.empty:
    metrics = calculate_performance_metrics(df_pnl["pnl"])
    
    # 5 Executive Bento Tiles
    b1, b2, b3, b4, b5 = st.columns(5)
    with b1:
        st.markdown(f"""
        <div class="bento-card">
            <div class="bento-label">SHARPE RATIO</div>
            <div class="bento-val">{metrics['sharpe_ratio']}</div>
            <div style="font-size: 0.72rem; color: #64748B;">Annualized (Rf=6%)</div>
        </div>
        """, unsafe_allow_html=True)
    with b2:
        st.markdown(f"""
        <div class="bento-card">
            <div class="bento-label">SORTINO RATIO</div>
            <div class="bento-val">{metrics['sortino_ratio']}</div>
            <div style="font-size: 0.72rem; color: #64748B;">Downside volatility adjusted</div>
        </div>
        """, unsafe_allow_html=True)
    with b3:
        st.markdown(f"""
        <div class="bento-card">
            <div class="bento-label">MAX DRAWDOWN</div>
            <div class="bento-val" style="color: #DC2626;">-{metrics['max_drawdown_bp']} <span style="font-size: 0.8rem;">bp</span></div>
            <div style="font-size: 0.72rem; color: #DC2626; font-weight: 700;">Peak-to-trough risk</div>
        </div>
        """, unsafe_allow_html=True)
    with b4:
        st.markdown(f"""
        <div class="bento-card">
            <div class="bento-label">WIN RATE</div>
            <div class="bento-val" style="color: #059669;">{metrics['win_rate_pct']}%</div>
            <div style="font-size: 0.72rem; color: #059669; font-weight: 700;">Profitable trading days</div>
        </div>
        """, unsafe_allow_html=True)
    with b5:
        st.markdown(f"""
        <div class="bento-card">
            <div class="bento-label">PROFIT FACTOR</div>
            <div class="bento-val">{metrics['profit_factor']}</div>
            <div style="font-size: 0.72rem; color: #64748B;">Gross profit / Gross loss</div>
        </div>
        """, unsafe_allow_html=True)

    # Cumulative Strategy Equity Curve
    st.markdown('<div class="bento-card" style="padding: 14px 18px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 0.9rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">📈 Cumulative Strategy Equity Curve (Basis Points Net Return)</div>', unsafe_allow_html=True)
    
    portfolio_pnl = df_pnl.groupby("trade_date")["pnl"].sum().reset_index()
    portfolio_pnl["cum_pnl"] = portfolio_pnl["pnl"].cumsum()
    
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(
        x=portfolio_pnl["trade_date"],
        y=portfolio_pnl["cum_pnl"],
        mode="lines",
        name="Cumulative Net P&L",
        line=dict(color="#10B981", width=2.4),
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.08)"
    ))
    
    fig_equity.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248, 250, 252, 0.7)",
        xaxis=dict(gridcolor="rgba(226, 232, 240, 0.8)"),
        yaxis=dict(title="Cumulative P&L (bp)", gridcolor="rgba(226, 232, 240, 0.8)")
    )
    st.plotly_chart(fig_equity, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Monthly Performance Heatmap Breakdown
    st.markdown('<div class="bento-card" style="padding: 14px 18px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 0.9rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">🗓️ Monthly Attribution Heatmap (P&L in Basis Points)</div>', unsafe_allow_html=True)
    
    portfolio_pnl["trade_date"] = pd.to_datetime(portfolio_pnl["trade_date"])
    portfolio_pnl["year"] = portfolio_pnl["trade_date"].dt.year
    portfolio_pnl["month"] = portfolio_pnl["trade_date"].dt.strftime("%b")
    
    monthly = portfolio_pnl.groupby(["year", "month"])["pnl"].sum().reset_index()
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_pivot = monthly.pivot(index="year", columns="month", values="pnl").reindex(columns=month_order).fillna(0)
    
    fig_heat = px.imshow(
        monthly_pivot,
        labels=dict(x="Month", y="Year", color="P&L (bp)"),
        color_continuous_scale="RdYlGn",
        text_auto=".1f"
    )
    fig_heat.update_layout(
        template="plotly_white",
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No backtest records found. Run pipeline scripts to populate.")