# GoldLens Terminal | Institutional MCX Relative Value & Arbitrage Desk

import os
import sys
import duckdb
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import streamlit as st

# 1. Guarantee project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.goldlens.db import (
    get_latest_prices,
    get_latest_rv_residuals,
    get_all_normalized_prices,
    get_all_rv_data,
    get_backtest_pnl,
    get_distinct_symbols,
    query_df
)
from src.goldlens.relval import calculate_performance_metrics, test_stationarity
from src.goldlens.costs import calculate_transaction_costs, estimate_roundtrip_cost_bp
from src.goldlens.alerts import evaluate_quiet_alert_gate

# 2. Page Configuration
st.set_page_config(
    page_title="GoldLens Terminal | Institutional MCX Arbitrage",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2.1 Brand Header (Renders directly above Home button in left taskbar)
logo_png = os.path.join(PROJECT_ROOT, "data", "goldlens_logo.png")
logo_svg = os.path.join(PROJECT_ROOT, "data", "goldlens_logo.svg")
logo_path = logo_png if os.path.exists(logo_png) else logo_svg
if os.path.exists(logo_path):
    st.logo(logo_path, size="large")

# 3. Master CSS Design System: 8-Style UI Fusion (Zero external folders)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    /* 1. Header & Toolbar Reset (Exposes Left Taskbar Toggle Button) */
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

    /* Left Taskbar Toggle Button (Streamlit 1.66 stExpandSidebarButton) */
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
    [data-testid="stExpandSidebarButton"] svg,
    button[aria-label="Expand sidebar"] svg {
        fill: #D97706 !important;
        color: #D97706 !important;
    }
    [data-testid="stExpandSidebarButton"]:hover,
    button[aria-label="Expand sidebar"]:hover {
        background: #FEF3C7 !important;
        transform: scale(1.08) !important;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, #F8FAFC 0%, #EDF2F7 90%);
        color: #0F172A;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
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
        max-width: 98% !important;
    }

    /* Collapse empty markdown containers produced by style injection */
    div[data-testid="element-container"]:has(style),
    div[data-testid="stMarkdownContainer"]:empty {
        display: none !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* Hide Streamlit header anchor links and fullscreen buttons */
    a.header-anchor, [data-testid="stHeaderActionElements"], .st-emotion-cache-15zrgzn {
        display: none !important;
    }

    /* 2. Glassmorphic Sidebar & Clean Brand Header Above Home Button */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(20px) saturate(190%);
        -webkit-backdrop-filter: blur(20px) saturate(190%);
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.02);
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

    /* 3. AnnSetu-Inspired Hero Welcome Card */
    .hero-banner {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.90) 0%, rgba(248, 250, 252, 0.82) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-top: 2px solid rgba(217, 119, 6, 0.45);
        border-radius: 20px;
        padding: 18px 24px;
        margin-top: 6px !important;
        margin-bottom: 14px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), inset 0 1px 1px rgba(255, 255, 255, 0.9);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 900;
        letter-spacing: -0.6px;
        color: #0F172A;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .hero-title .gold-gradient {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        color: #64748B;
        font-size: 0.88rem;
        font-weight: 500;
        margin-top: 4px;
    }

    /* 4. Claymorphic & Liquid Glass Pills */
    .pill-telemetry {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 40px;
        font-size: 0.8rem;
        font-weight: 700;
        background: #FFFFFF;
        box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.04), -3px -3px 8px rgba(255, 255, 255, 0.9), inset 1px 1px 2px rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(226, 232, 240, 0.8);
        color: #334155;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 10px #10B981;
        animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.2); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }

    /* 5. Bento Grid Modular Cards */
    .bento-card {
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-top: 1.5px solid rgba(255, 255, 255, 1);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
        transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .bento-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 32px -8px rgba(217, 119, 6, 0.12);
        border-color: rgba(217, 119, 6, 0.35);
    }

    .bento-header-label {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: #64748B;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .bento-price-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        margin: 6px 0 4px 0;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.6px;
    }
    .bento-subtext {
        font-size: 0.75rem;
        color: #64748B;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 6. Brutalist High-Contrast Status Badges */
    .badge-rich {
        background: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
        padding: 3px 9px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-cheap {
        background: #D1FAE5;
        color: #065F46;
        border: 1px solid #6EE7B7;
        padding: 3px 9px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-fair {
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
        padding: 3px 9px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* 7. AnnSetu Quick Actions Command Dock */
    .dock-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
        margin-top: 14px;
        margin-bottom: 8px;
    }
    .dock-btn {
        background: #FFFFFF;
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 16px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.03), -3px -3px 8px rgba(255, 255, 255, 0.95), inset 1px 1px 2px rgba(255, 255, 255, 0.8);
        transition: all 0.2s ease;
        text-decoration: none;
        color: #1E293B;
        cursor: pointer;
    }
    .dock-btn:hover {
        transform: translateY(-2px);
        border-color: rgba(217, 119, 6, 0.4);
        box-shadow: 0 8px 20px -4px rgba(217, 119, 6, 0.15);
    }
    .dock-icon {
        font-size: 1.4rem;
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
    }
    .dock-text-title {
        font-size: 0.85rem;
        font-weight: 800;
        color: #0F172A;
    }
    .dock-text-sub {
        font-size: 0.72rem;
        color: #64748B;
        font-weight: 500;
    }

    /* 8. Modern Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(241, 245, 249, 0.7);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 18px;
        font-weight: 700;
        font-size: 0.88rem;
        color: #475569;
        border: none !important;
        background: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #D97706 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }

    /* Section Header */
    .section-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #0F172A;
        margin: 14px 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 4. Fetch Live Database Records
latest_df = get_latest_prices()
rv_latest = get_latest_rv_residuals()
symbols = get_distinct_symbols()

# Benchmark Rate Calculation
benchmark_rate = latest_df["close_pg"].mean() if not latest_df.empty else 7500.0

# 5. AnnSetu-Inspired Hero Header Banner
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">
            🏆 GoldLens <span class="gold-gradient">Command Center</span>
        </div>
        <div class="hero-sub">
            Institutional Relative Value Analytics & Multi-Contract Arbitrage Engine • MCX India
        </div>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <div class="pill-telemetry">
            <div class="live-dot"></div>
            <span>MCX LIVE ENGINE</span>
        </div>
        <div class="pill-telemetry">
            <span>🥇 PURE BENCHMARK:</span>
            <strong style="color: #D97706; font-family: 'JetBrains Mono', monospace;">₹{benchmark_rate:,.2f}/g</strong>
        </div>
        <div class="pill-telemetry">
            <span>ACTIVE DERIVATIVES:</span>
            <strong>{len(latest_df)} CONTRACTS</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. Sidebar Controls & Market Friction Gates
with st.sidebar:
    st.markdown("### ⚙️ Relative Value Parameters")
    z_entry = st.slider("🎯 Z-Score Entry Threshold (σ)", 1.0, 3.5, 2.0, 0.1)
    z_exit = st.slider("🚪 Z-Score Exit Gate (σ)", 0.0, 1.5, 0.5, 0.1)
    
    st.markdown("---")
    st.markdown("### 💸 Friction & Execution Cost")
    brokerage_fee = st.number_input("Brokerage Fee (₹/order)", 0.0, 100.0, 20.0, 5.0)
    slippage_buffer_ticks = st.slider("Slippage Buffer (Ticks)", 0, 5, 1)
    ctt_rate = st.number_input("CTT Rate (%)", 0.005, 0.05, 0.010, 0.001) / 100.0
    
    st.markdown("---")
    st.markdown("### 🛡️ Quiet Alert Filter")
    quiet_filter_enabled = st.checkbox("Enforce Edge > Friction Rule", value=True)
    st.caption("Quiet Alert gate silences false positives when theoretical RV edge fails to surpass roundtrip execution friction.")

# 7. Dashboard Multi-Tab Architecture
tab_terminal, tab_compare, tab_backtest, tab_friction = st.tabs([
    "👑 Terminal Cockpit", 
    "⚖️ Pair Arbitrage Lab", 
    "📊 Backtest & Risk Engine", 
    "🧮 Friction & Slippage Simulator"
])

# ==============================================================================
# TAB 1: 👑 TERMINAL COCKPIT
# ==============================================================================
with tab_terminal:
    # Bento Ticker Row
    st.markdown('<div class="section-title">📊 Multi-Contract Normalized Basis Telemetry</div>', unsafe_allow_html=True)
    
    if not latest_df.empty:
        # Merge latest prices with rv residuals
        merged_cards = pd.merge(latest_df, rv_latest[["symbol", "resid_bp", "z_score"]], on="symbol", how="left")
        
        cols = st.columns(len(merged_cards))
        for idx, row in merged_cards.iterrows():
            sym = row["symbol"]
            close_pg = row["close_pg"]
            quote_close = row["close"]
            z = row["z_score"] if pd.notnull(row["z_score"]) else 0.0
            resid = row["resid_bp"] if pd.notnull(row["resid_bp"]) else 0.0
            
            # Badge logic
            if z >= z_entry:
                badge_html = f'<span class="badge-rich">RICH +{z:.2f}σ</span>'
            elif z <= -z_entry:
                badge_html = f'<span class="badge-cheap">CHEAP {z:.2f}σ</span>'
            else:
                badge_html = f'<span class="badge-fair">FAIR {z:+.2f}σ</span>'
                
            spec_desc = {
                "GOLDM": "100g Unit • 0.995 Fineness",
                "GOLDTEN": "10g Unit • 0.999 Fineness",
                "GOLDGUINEA": "8g Unit • 0.999 Fineness",
                "GOLDPETAL": "1g Unit • 0.999 Fineness"
            }.get(sym, "MCX Gold Contract")
            
            with cols[idx]:
                st.markdown(f"""
                <div class="bento-card">
                    <div class="bento-header-label">
                        <span>🥇 {sym}</span>
                        {badge_html}
                    </div>
                    <div class="bento-price-val">₹{close_pg:,.2f}<span style="font-size: 0.8rem; color: #64748B; font-weight: 600;">/g</span></div>
                    <div class="bento-subtext">
                        <span>Quote: <strong>₹{quote_close:,.0f}</strong></span>
                        <span>•</span>
                        <span>OI: {row['oi']:,}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 6px; font-weight: 600;">
                        {spec_desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No latest contract data found. Pipeline will load upon refresh.")

    # Spatial Centerstage (AnnSetu Pattern: Left Visual Map/Curve + Right Actionable Opportunities Feed)
    st.markdown('<div class="section-title" style="margin-top: 18px;">🎯 Spatial RV Centerstage: Term Structure & Opportunity Feed</div>', unsafe_allow_html=True)
    
    col_curve, col_feed = st.columns([1.6, 1.0])
    
    with col_curve:
        st.markdown('<div class="bento-card" style="padding: 12px 16px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.85rem; font-weight: 800; color: #0F172A; margin-bottom: 6px;">📈 MCX Gold Term Structure & Log-Carry Regression Curve</div>', unsafe_allow_html=True)
        
        # Plot Carry Curve (DTE vs Pure Basis)
        if not latest_df.empty:
            fig_carry = go.Figure()
            
            # Bubble scatter of contracts
            for sym in latest_df["symbol"]:
                sub = latest_df[latest_df["symbol"] == sym]
                fig_carry.add_trace(go.Scatter(
                    x=sub["dte"],
                    y=sub["close_pg"],
                    mode="markers+text",
                    name=sym,
                    text=[sym],
                    textposition="top center",
                    marker=dict(
                        size=np.clip(np.sqrt(sub["oi"].values[0]) / 8, 14, 34),
                        color=["#D97706", "#2563EB", "#059669", "#7C3AED"][list(latest_df["symbol"]).index(sym) % 4],
                        line=dict(width=2, color="#FFFFFF")
                    ),
                    hovertemplate=f"<b>{sym}</b><br>DTE: %{{x}} days<br>Pure Basis: ₹%{{y:,.2f}}/g<br>OI: {sub['oi'].values[0]:,}<extra></extra>"
                ))
                
            fig_carry.update_layout(
                template="plotly_white",
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248, 250, 252, 0.7)",
                xaxis=dict(title="Days to Expiry (DTE)", gridcolor="rgba(226, 232, 240, 0.8)", zeroline=False),
                yaxis=dict(title="₹ / Gram Pure Gold", gridcolor="rgba(226, 232, 240, 0.8)", zeroline=False),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_carry, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Historical Z-Scores plot below
        st.markdown('<div class="bento-card" style="padding: 12px 16px; margin-top: 12px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.85rem; font-weight: 800; color: #0F172A; margin-bottom: 6px;">📉 60-Day Rolling Z-Score Deviation Matrix</div>', unsafe_allow_html=True)
        
        all_rv = get_all_rv_data()
        if not all_rv.empty:
            fig_z = go.Figure()
            colors = ["#D97706", "#2563EB", "#059669", "#7C3AED"]
            
            for idx, sym in enumerate(all_rv["symbol"].unique()):
                sub = all_rv[all_rv["symbol"] == sym]
                fig_z.add_trace(go.Scatter(
                    x=sub["trade_date"],
                    y=sub["z_score"],
                    name=sym,
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))
                
            # Gate boundaries
            fig_z.add_hline(y=z_entry, line_dash="dash", line_color="#DC2626", annotation_text=f"+{z_entry}σ Rich Gate")
            fig_z.add_hline(y=-z_entry, line_dash="dash", line_color="#10B981", annotation_text=f"-{z_entry}σ Cheap Gate")
            fig_z.add_hline(y=0, line_dash="dot", line_color="#94A3B8")
            
            fig_z.update_layout(
                template="plotly_white",
                height=260,
                margin=dict(l=20, r=20, t=15, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248, 250, 252, 0.7)",
                xaxis=dict(gridcolor="rgba(226, 232, 240, 0.8)"),
                yaxis=dict(title="Z-Score (σ)", gridcolor="rgba(226, 232, 240, 0.8)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_z, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_feed:
        st.markdown('<div class="bento-card" style="padding: 14px 16px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.88rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">⚡ Actionable Arbitrage Signals (Quiet Gate Filtered)</div>', unsafe_allow_html=True)
        
        # Calculate pair spreads & Quiet Alert evaluations
        if len(latest_df) >= 2:
            pairs_data = []
            sym_list = list(latest_df["symbol"])
            price_map = dict(zip(latest_df["symbol"], latest_df["close_pg"]))
            
            for i in range(len(sym_list)):
                for j in range(i + 1, len(sym_list)):
                    s1, s2 = sym_list[i], sym_list[j]
                    p1, p2 = price_map[s1], price_map[s2]
                    spread = p1 - p2
                    # Approximate theoretical basis points edge
                    exp_edge_bp = abs(spread / ((p1 + p2) / 2)) * 10000
                    cost_bp = estimate_roundtrip_cost_bp(brokerage_fee, slippage_buffer_ticks, 75000.0)
                    net_edge = exp_edge_bp - cost_bp
                    
                    # Gate Check
                    is_actionable = (net_edge > 0) and (exp_edge_bp > 5.0) if quiet_filter_enabled else (exp_edge_bp > 2.0)
                    
                    pairs_data.append({
                        "pair": f"{s1} / {s2}",
                        "spread": spread,
                        "edge_bp": exp_edge_bp,
                        "cost_bp": cost_bp,
                        "net_edge": net_edge,
                        "actionable": is_actionable
                    })
                    
            pairs_df = pd.DataFrame(pairs_data).sort_values(by="net_edge", ascending=False)
            
            for _, row in pairs_df.iterrows():
                pair_name = row["pair"]
                spread = row["spread"]
                net_edge = row["net_edge"]
                edge_bp = row["edge_bp"]
                cost_bp = row["cost_bp"]
                actionable = row["actionable"]
                
                status_pill = '<span class="badge-cheap">✅ ACTIONABLE</span>' if actionable else '<span class="badge-rich">🛑 FILTERED</span>'
                badge_bg = "rgba(16, 185, 129, 0.08)" if actionable else "rgba(241, 245, 249, 0.6)"
                border_color = "rgba(16, 185, 129, 0.3)" if actionable else "rgba(226, 232, 240, 0.8)"
                
                st.markdown(f"""
                <div style="background: {badge_bg}; border: 1px solid {border_color}; border-radius: 14px; padding: 10px 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #0F172A; font-size: 0.85rem;">{pair_name}</strong>
                        {status_pill}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; font-weight: 800; color: #1E293B;">
                            ₹{spread:+.2f}/g spread
                        </span>
                        <span style="font-size: 0.75rem; color: #64748B;">
                            Gross: <strong>{edge_bp:.1f} bp</strong> • Cost: <strong>{cost_bp:.1f} bp</strong>
                        </span>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.72rem; color: {'#065F46' if net_edge > 0 else '#991B1B'}; font-weight: 700;">
                        Net Edge after friction: {net_edge:+.1f} bp
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # AnnSetu Quick Actions Command Dock
    st.markdown('<div class="section-title">⚡ Command Dock: Quick Execution Actions</div>', unsafe_allow_html=True)
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.markdown("""
        <div class="dock-btn">
            <div class="dock-icon">⚖️</div>
            <div>
                <div class="dock-text-title">Delta Sizing Lab</div>
                <div class="dock-text-sub">Evaluate neutral ratio</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_d2:
        st.markdown("""
        <div class="dock-btn">
            <div class="dock-icon">🔍</div>
            <div>
                <div class="dock-text-title">ADF Stationarity</div>
                <div class="dock-text-sub">P-Value unit root test</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_d3:
        st.markdown("""
        <div class="dock-btn">
            <div class="dock-icon">📊</div>
            <div>
                <div class="dock-text-title">Quant Performance</div>
                <div class="dock-text-sub">Sharpe & max drawdown</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_d4:
        st.markdown("""
        <div class="dock-btn">
            <div class="dock-icon">🔄</div>
            <div>
                <div class="dock-text-title">DuckDB Pipeline</div>
                <div class="dock-text-sub">Synchronize 3,980 rows</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# TAB 2: ⚖️ PAIR ARBITRAGE & SIZING LAB
# ==============================================================================
with tab_compare:
    st.markdown('<div class="section-title">⚖️ Statistical Pair Arbitrage & Delta-Neutral Sizing Engine</div>', unsafe_allow_html=True)
    
    if len(symbols) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            leg1 = st.selectbox("Select Primary Contract (Leg 1)", symbols, index=0)
        with c2:
            leg2 = st.selectbox("Select Hedge Contract (Leg 2)", symbols, index=1 if len(symbols) > 1 else 0)
            
        if leg1 == leg2:
            st.warning("⚠️ Please select two different contracts to calculate statistical pair spread.")
        else:
            # Query price data for selected pair
            sql_pair = f"""
                SELECT p1.trade_date, p1.close_pg as p1_close, p2.close_pg as p2_close,
                       (p1.close_pg - p2.close_pg) as spread_pg
                FROM prices_norm p1
                JOIN prices_norm p2 ON p1.trade_date = p2.trade_date
                WHERE p1.symbol = '{leg1}' AND p2.symbol = '{leg2}'
                ORDER BY p1.trade_date
            """
            df_pair = query_df(sql_pair)
            
            if not df_pair.empty:
                latest_spread = df_pair.iloc[-1]["spread_pg"]
                mean_spread = df_pair["spread_pg"].mean()
                std_spread = df_pair["spread_pg"].std()
                z_dev = (latest_spread - mean_spread) / std_spread if std_spread != 0 else 0.0
                
                # Top Stat Pills
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f"""
                    <div class="bento-card">
                        <div class="bento-header-label">CURRENT SPREAD</div>
                        <div class="bento-price-val">₹{latest_spread:+.2f}<span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                        <div class="bento-subtext">Latest pure gold basis gap</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                    <div class="bento-card">
                        <div class="bento-header-label">HISTORICAL MEAN</div>
                        <div class="bento-price-val">₹{mean_spread:+.2f}<span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                        <div class="bento-subtext">Long-term equilibrium</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m3:
                    st.markdown(f"""
                    <div class="bento-card">
                        <div class="bento-header-label">SPREAD VOLATILITY (1σ)</div>
                        <div class="bento-price-val">₹{std_spread:.2f}<span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                        <div class="bento-subtext">Standard deviation band</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m4:
                    tag_class = "badge-rich" if z_dev > 1.5 else ("badge-cheap" if z_dev < -1.5 else "badge-fair")
                    st.markdown(f"""
                    <div class="bento-card">
                        <div class="bento-header-label">CURRENT Z-SCORE</div>
                        <div class="bento-price-val">{z_dev:+.2f}σ</div>
                        <div class="bento-subtext"><span class="{tag_class}">{"OVERVALUED" if z_dev > 1.5 else ("UNDERVALUED" if z_dev < -1.5 else "FAIR VALUE")}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                # Pair Spread Chart with +/- 2 Sigma Bands
                st.markdown('<div class="bento-card" style="margin-top: 14px; padding: 12px 18px;">', unsafe_allow_html=True)
                fig_spread = go.Figure()
                fig_spread.add_trace(go.Scatter(
                    x=df_pair["trade_date"], 
                    y=df_pair["spread_pg"], 
                    name=f"{leg1} - {leg2} Spread",
                    line=dict(color="#D97706", width=2.2)
                ))
                fig_spread.add_hline(y=mean_spread, line_dash="dash", line_color="#64748B", annotation_text="Mean Spread")
                fig_spread.add_hline(y=mean_spread + 2 * std_spread, line_dash="dot", line_color="#DC2626", annotation_text="+2σ Upper Bound")
                fig_spread.add_hline(y=mean_spread - 2 * std_spread, line_dash="dot", line_color="#10B981", annotation_text="-2σ Lower Bound")
                
                fig_spread.update_layout(
                    template="plotly_white",
                    height=360,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248, 250, 252, 0.7)",
                    xaxis=dict(gridcolor="rgba(226, 232, 240, 0.8)"),
                    yaxis=dict(title="Spread (₹/g Pure Gold)", gridcolor="rgba(226, 232, 240, 0.8)")
                )
                st.plotly_chart(fig_spread, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Interactive Delta-Neutral Sizing Calculator
                st.markdown('<div class="section-title">🧮 Delta-Neutral Order Ticket & Friction Analysis</div>', unsafe_allow_html=True)
                
                col_lot1, col_lot2 = st.columns(2)
                with col_lot1:
                    st.markdown('<div class="bento-card">', unsafe_allow_html=True)
                    leg1_lots = st.number_input(f"Enter Lots for {leg1}", min_value=1, max_value=1000, value=1)
                    
                    mult_map = {"GOLDM": 100, "GOLDTEN": 10, "GOLDGUINEA": 8, "GOLDPETAL": 1}
                    g1 = mult_map.get(leg1, 10) * leg1_lots
                    g2_mult = mult_map.get(leg2, 1)
                    required_leg2_lots = g1 / g2_mult
                    
                    st.markdown(f"""
                    <div style="background: rgba(217, 119, 6, 0.08); border: 1px solid rgba(217, 119, 6, 0.3); border-radius: 12px; padding: 12px 14px; margin-top: 10px;">
                        <strong style="color: #92400E; font-size: 0.88rem;">💡 Delta-Neutral Hedge Ratio:</strong>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 4px 0;">
                            Trade <strong>{required_leg2_lots:.1f} lots</strong> of {leg2}
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B;">
                            Achieves exact weight neutrality across {g1:,} pure grams of physical gold.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_lot2:
                    st.markdown('<div class="bento-card">', unsafe_allow_html=True)
                    notional = g1 * (df_pair.iloc[-1]["p1_close"] if not df_pair.empty else 7500.0)
                    cost_info = calculate_transaction_costs(notional, True, {
                        "costs": {
                            "brokerage_per_order_inr": brokerage_fee,
                            "gst_rate": 0.18,
                            "ctt_rate": ctt_rate,
                            "stamp_duty_rate": 0.00003,
                            "slippage_ticks": slippage_buffer_ticks
                        }
                    })
                    
                    exp_edge_bp = abs(z_dev * 14.0)
                    cost_bp = cost_info["cost_bp"] * 2 # roundtrip
                    net_edge = exp_edge_bp - cost_bp
                    
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; font-weight: 800; color: #64748B; text-transform: uppercase;">ROUNDTRIP EXECUTION FRICTION</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #0F172A; font-family: 'JetBrains Mono', monospace; margin: 4px 0;">
                        ₹{cost_info['total_cost_inr'] * 2:,.2f} <span style="font-size: 0.8rem; color: #64748B;">({cost_bp:.1f} bp)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #475569; margin-top: 8px;">
                        <span>Theoretical Gross Edge:</span>
                        <strong>+{exp_edge_bp:.1f} bp</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #475569; margin-top: 4px;">
                        <span>Net Edge after Statutory Fees:</span>
                        <strong style="color: {'#059669' if net_edge > 0 else '#DC2626'};">{net_edge:+.1f} bp</strong>
                    </div>
                    <div style="margin-top: 10px;">
                        {"<span class='badge-cheap'>✅ Actionable Arbitrage Edge Exceeds Cost</span>" if net_edge > 0 else "<span class='badge-rich'>🛑 Filtered by Quiet Alert Gate (Edge < Cost)</span>"}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 3: 📊 WALK-FORWARD BACKTEST & RISK ENGINE
# ==============================================================================
with tab_backtest:
    st.markdown('<div class="section-title">📊 Quantitative Performance Attribution & Risk Engine</div>', unsafe_allow_html=True)
    st.caption("Institutional Walk-Forward Strategy Simulation with Zero Look-Ahead Bias (Strict t+1 Execution Fills)")
    
    df_pnl = get_backtest_pnl()
    
    if not df_pnl.empty:
        metrics = calculate_performance_metrics(df_pnl["pnl"])
        
        # 5 Executive Bento Tiles
        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            st.markdown(f"""
            <div class="bento-card">
                <div class="bento-header-label">SHARPE RATIO</div>
                <div class="bento-price-val">{metrics['sharpe_ratio']}</div>
                <div class="bento-subtext">Annualized risk-adjusted</div>
            </div>
            """, unsafe_allow_html=True)
        with b2:
            st.markdown(f"""
            <div class="bento-card">
                <div class="bento-header-label">SORTINO RATIO</div>
                <div class="bento-price-val">{metrics['sortino_ratio']}</div>
                <div class="bento-subtext">Downside penalty adjusted</div>
            </div>
            """, unsafe_allow_html=True)
        with b3:
            st.markdown(f"""
            <div class="bento-card">
                <div class="bento-header-label">MAX DRAWDOWN</div>
                <div class="bento-price-val" style="color: #DC2626;">-{metrics['max_drawdown_bp']} <span style="font-size: 0.8rem;">bp</span></div>
                <div class="bento-subtext">Peak-to-trough drop</div>
            </div>
            """, unsafe_allow_html=True)
        with b4:
            st.markdown(f"""
            <div class="bento-card">
                <div class="bento-header-label">WIN RATE</div>
                <div class="bento-price-val" style="color: #059669;">{metrics['win_rate_pct']}%</div>
                <div class="bento-subtext">Profitable trades ratio</div>
            </div>
            """, unsafe_allow_html=True)
        with b5:
            st.markdown(f"""
            <div class="bento-card">
                <div class="bento-header-label">PROFIT FACTOR</div>
                <div class="bento-price-val">{metrics['profit_factor']}</div>
                <div class="bento-subtext">Gross wins / Gross losses</div>
            </div>
            """, unsafe_allow_html=True)

        # Cumulative Strategy Equity Curve
        st.markdown('<div class="bento-card" style="margin-top: 14px; padding: 12px 18px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.88rem; font-weight: 800; color: #0F172A; margin-bottom: 6px;">📈 Cumulative Strategy Net P&L Equity Curve (Basis Points)</div>', unsafe_allow_html=True)
        
        # Aggregate daily portfolio pnl
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
            height=360,
            margin=dict(l=20, r=20, t=15, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248, 250, 252, 0.7)",
            xaxis=dict(gridcolor="rgba(226, 232, 240, 0.8)"),
            yaxis=dict(title="Cumulative P&L (bp)", gridcolor="rgba(226, 232, 240, 0.8)")
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Monthly Performance Breakdown
        st.markdown('<div class="bento-card" style="margin-top: 14px; padding: 12px 18px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.88rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">🗓️ Monthly Returns Heatmap (Basis Points Attribution)</div>', unsafe_allow_html=True)
        
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
            margin=dict(l=20, r=20, t=15, b=20),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 4: 🧮 FRICTION & SLIPPAGE SIMULATOR
# ==============================================================================
with tab_friction:
    st.markdown('<div class="section-title">🧮 Market Microstructure Friction & Slippage Simulator</div>', unsafe_allow_html=True)
    st.caption("Detailed breakdown of statutory levies: MCX Commodity Transaction Tax (CTT), GST, Stamp Duty, Brokerage, and Tick Slippage.")
    
    col_f1, col_f2 = st.columns([1.2, 1.8])
    with col_f1:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        sim_notional = st.number_input("Simulated Trade Notional (₹)", min_value=10000.0, max_value=5000000.0, value=750000.0, step=50000.0)
        sim_ticks = st.slider("Simulated Slippage (Ticks)", 0, 5, 1)
        sim_brokerage = st.slider("Brokerage / Order (₹)", 10.0, 50.0, 20.0, 5.0)
        
        cost_sim = calculate_transaction_costs(sim_notional, True, {
            "costs": {
                "brokerage_per_order_inr": sim_brokerage,
                "gst_rate": 0.18,
                "ctt_rate": ctt_rate,
                "stamp_duty_rate": 0.00003,
                "slippage_ticks": sim_ticks
            }
        })
        
        st.markdown(f"""
        <div style="margin-top: 12px; padding: 12px; background: rgba(248, 250, 252, 0.9); border-radius: 12px; border: 1px solid #E2E8F0;">
            <div style="font-size: 0.75rem; color: #64748B; font-weight: 700;">TOTAL ESTIMATED ONE-WAY FRICTION:</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #D97706; font-family: 'JetBrains Mono', monospace; margin: 4px 0;">
                ₹{cost_sim['total_cost_inr']:,.2f}
            </div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #334155;">
                Friction in Basis Points: <span style="font-family: 'JetBrains Mono', monospace;">{cost_sim['cost_bp']:.2f} bp</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_f2:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.88rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">📊 Statutory Fee Breakdown Matrix</div>', unsafe_allow_html=True)
        
        fee_data = [
            {"Fee Category": "Brokerage (Flat)", "Amount (₹)": cost_sim["brokerage"], "Basis": "Fixed per executed order"},
            {"Fee Category": "GST (18% on Brokerage)", "Amount (₹)": cost_sim["gst"], "Basis": "Statutory Goods & Services Tax"},
            {"Fee Category": "CTT (0.01% on Sell)", "Amount (₹)": cost_sim["ctt"], "Basis": "Commodity Transaction Tax"},
            {"Fee Category": "Stamp Duty (0.003%)", "Amount (₹)": cost_sim["stamp_duty"], "Basis": "State Stamp Duty levy"},
            {"Fee Category": "Slippage Impact", "Amount (₹)": cost_sim["slippage"], "Basis": f"{sim_ticks} tick(s) market buffer"}
        ]
        st.dataframe(pd.DataFrame(fee_data), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)