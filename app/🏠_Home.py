# Step 5: Streamlit main dashboard

import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(
    page_title="GoldLens Terminal | MCX Intelligence",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling: Complete Glassmorphic Bento Grid + Zero Top Margin Fix
st.markdown("""
<style>
    /* 1. Hide Streamlit Top Header Bar & Deploy Button */
    header[data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* 2. Remove All Top Margins & Padding (Force Content to Top Edge) */
    .stApp {
        background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%);
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        margin-top: -3.5rem !important;
    }

    /* 3. Fix Sidebar Navigation Position & Gaps */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.70) !important;
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.8) !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0rem !important;
        margin-top: -3rem !important;
    }

    /* 4. Bento Grid Glass Card Styling */
    .bento-glass-card {
        background: rgba(255, 255, 255, 0.80);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05), 0 4px 10px -2px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .bento-glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 35px -10px rgba(217, 119, 6, 0.15);
        border-color: rgba(217, 119, 6, 0.4);
    }

    /* 5. Typography & Badges */
    .bento-label {
        font-size: 0.75rem;
        color: #64748B;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .bento-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #0F172A;
        margin: 6px 0;
        letter-spacing: -0.5px;
    }
    .bento-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 10px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 600;
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
        border: 1px solid rgba(217, 119, 6, 0.2);
    }

    .spatial-header {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0F172A;
        margin: 18px 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Header (Starting Right at Top)
st.markdown("""
<div style="margin-bottom: 16px; padding-top: 0px;">
    <h1 style="font-size: 2.1rem; font-weight: 900; color: #0F172A; margin:0; letter-spacing: -0.8px;">
        🏠 GoldLens <span style="background: linear-gradient(135deg, #D97706 0%, #B45309 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Analytics Command Center</span>
    </h1>
    <p style="color: #64748B; font-size: 0.92rem; margin-top: 4px; font-weight: 500;">
        Institutional MCX Relative Value Engine • Bento-Grid Spatial Dashboard
    </p>
</div>
""", unsafe_allow_html=True)

# Database Connection
db_path = "data/processed/goldlens.duckdb"
conn = duckdb.connect(db_path)

# 1. Bento Ticker Row
try:
    latest_prices = conn.execute("""
        SELECT symbol, close_pg, close, trade_date 
        FROM prices_norm 
        WHERE trade_date = (SELECT MAX(trade_date) FROM prices_norm)
        ORDER BY symbol
    """).fetchdf()

    if not latest_prices.empty:
        cols = st.columns(len(latest_prices))
        for idx, row in latest_prices.iterrows():
            with cols[idx]:
                st.markdown(f"""
                <div class="bento-glass-card">
                    <div class="bento-label">🥇 {row['symbol']} • Pure Basis</div>
                    <div class="bento-value">₹{row['close_pg']:,.2f} <span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                    <div class="bento-badge">Quote: ₹{row['close']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Run pipeline scripts to populate ticker metrics.")
except Exception:
    st.info("ℹ️ Run data pipeline scripts to initialize ticker cards.")

# 2. Sidebar Controls
st.sidebar.markdown("### ⚙️ Signal Gates")
entry_z = st.sidebar.slider("🎯 Z-Score Entry Gate", 1.0, 3.0, 2.0, 0.1)
exit_z = st.sidebar.slider("🚪 Z-Score Exit Gate", 0.0, 1.0, 0.5, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💸 Market Friction")
brokerage = st.sidebar.number_input("Brokerage Fee (₹/order)", 0.0, 100.0, 20.0)
slippage_ticks = st.sidebar.slider("Slippage Buffer (Ticks)", 0, 5, 1)

# 3. Main Chart: Normalized Prices
st.markdown('<div class="spatial-header">📈 Normalized Contract Price Overlay (₹ / Pure Gram Gold)</div>', unsafe_allow_html=True)

st.markdown('<div class="bento-glass-card" style="padding: 12px;">', unsafe_allow_html=True)
try:
    df_norm = conn.execute("SELECT trade_date, symbol, close_pg FROM prices_norm ORDER BY trade_date").fetchdf()
    
    fig_norm = go.Figure()
    colors = ['#D97706', '#059669', '#2563EB', '#7C3AED']
    
    for idx, sym in enumerate(df_norm['symbol'].unique()):
        sub_df = df_norm[df_norm['symbol'] == sym]
        fig_norm.add_trace(go.Scatter(
            x=sub_df['trade_date'], 
            y=sub_df['close_pg'], 
            mode='lines', 
            name=sym,
            line=dict(color=colors[idx % len(colors)], width=2.5)
        ))
    
    fig_norm.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.5)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_norm, use_container_width=True)
except Exception:
    st.warning("Awaiting normalized data...")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Main Chart: Z-Scores & Residuals
st.markdown('<div class="spatial-header">📊 Relative Value Residuals & Rolling Z-Score Signals</div>', unsafe_allow_html=True)

st.markdown('<div class="bento-glass-card" style="padding: 12px;">', unsafe_allow_html=True)
try:
    df_rv = conn.execute("SELECT trade_date, symbol, resid_bp, z_score FROM rv_daily ORDER BY trade_date").fetchdf()
    
    fig_z = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("Model Residuals (Basis Points)", "60-Day Rolling Z-Score"))
    
    for idx, sym in enumerate(df_rv['symbol'].unique()):
        sub_rv = df_rv[df_rv['symbol'] == sym]
        fig_z.add_trace(go.Scatter(x=sub_rv['trade_date'], y=sub_rv['resid_bp'], name=sym, line=dict(width=1.5)), row=1, col=1)
        fig_z.add_trace(go.Scatter(x=sub_rv['trade_date'], y=sub_rv['z_score'], name=sym, showlegend=False, line=dict(width=1.5)), row=2, col=1)
    
    # Threshold Lines
    fig_z.add_hline(y=entry_z, line_dash="dash", line_color="#DC2626", row=2, col=1, annotation_text="+Entry Gate")
    fig_z.add_hline(y=-entry_z, line_dash="dash", line_color="#16A34A", row=2, col=1, annotation_text="-Entry Gate")
    
    fig_z.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.5)'
    )
    st.plotly_chart(fig_z, use_container_width=True)
except Exception:
    st.info("Run `python -m src.goldlens.curve` to refresh Z-score signals.")
st.markdown('</div>', unsafe_allow_html=True)

conn.close()