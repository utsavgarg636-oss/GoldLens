# GoldLens | Pair Arbitrage & Delta-Neutral Sizing Desk

import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# 1. Guarantee project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.goldlens.db import get_distinct_symbols, query_df
from src.goldlens.costs import calculate_transaction_costs, estimate_roundtrip_cost_bp

st.set_page_config(
    page_title="GoldLens | Pair Arbitrage Desk",
    page_icon="⚖️",
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
        background: 
            radial-gradient(at 0% 0%, rgba(224, 242, 254, 0.50) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(254, 243, 199, 0.45) 0px, transparent 45%),
            radial-gradient(at 50% 50%, rgba(243, 232, 255, 0.35) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(209, 250, 229, 0.40) 0px, transparent 50%),
            radial-gradient(at 0% 100%, rgba(255, 237, 213, 0.45) 0px, transparent 45%),
            #F8FAFC !important;
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
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-top: 1.5px solid rgba(255, 255, 255, 1);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
        transition: all 0.28s ease;
    }
    .bento-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px -6px rgba(15, 23, 42, 0.08);
    }
    .bento-card-cyan-tint {
        background: linear-gradient(135deg, rgba(240, 249, 255, 0.88) 0%, rgba(224, 242, 254, 0.58) 100%) !important;
        border: 1px solid rgba(14, 165, 233, 0.30) !important;
    }
    .bento-card-slate-tint {
        background: linear-gradient(135deg, rgba(248, 250, 252, 0.92) 0%, rgba(241, 245, 249, 0.70) 100%) !important;
        border: 1px solid rgba(203, 213, 225, 0.65) !important;
    }
    .bento-card-amber-tint {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(254, 243, 199, 0.40) 100%) !important;
        border: 1px solid rgba(217, 119, 6, 0.28) !important;
    }
    .bento-card-purple-tint {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(243, 232, 255, 0.38) 100%) !important;
        border: 1px solid rgba(168, 85, 247, 0.28) !important;
    }
    .bento-card-blue-tint {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(224, 242, 254, 0.38) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.28) !important;
    }
    .bento-card-mint-tint {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(209, 250, 229, 0.38) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.28) !important;
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

    /* Dynamic Parameter Change Highlights (1-Second Smooth Flash) */
    @keyframes glHighlightPulse {
        0% {
            background-color: #FEF08A !important;
            color: #92400E !important;
            box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.45), 0 2px 10px rgba(245, 158, 11, 0.35) !important;
            border-radius: 6px;
            transform: scale(1.06);
        }
        35% {
            background-color: #FEF9C3 !important;
            color: #92400E !important;
            box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.28), 0 2px 6px rgba(245, 158, 11, 0.20) !important;
            transform: scale(1.03);
        }
        100% {
            background-color: transparent !important;
            color: inherit !important;
            box-shadow: none !important;
            transform: scale(1.0);
        }
    }

    .gl-flash-0, .gl-flash-1 {
        display: inline-block;
        padding: 1px 6px;
        margin: -1px -2px;
        border-radius: 6px;
        animation: glHighlightPulse 1.25s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    }
</style>
""", unsafe_allow_html=True)

# Dynamic Parameter Change Detection Helper
def get_change_flash_class(key: str, current_val) -> str:
    """
    Returns an alternating flash CSS class ('gl-flash-0' or 'gl-flash-1') if current_val has changed
    compared to the previous run, or '' if it hasn't changed.
    Triggers a 1-second highlight animation exactly once upon value modification.
    """
    state_key = f"_prev_{key}"
    counter_key = f"_flash_cnt_{key}"
    prev_val = st.session_state.get(state_key, None)
    has_changed = (prev_val is not None and prev_val != current_val)
    st.session_state[state_key] = current_val
    if has_changed:
        cnt = st.session_state.get(counter_key, 0) + 1
        st.session_state[counter_key] = cnt
        return f"gl-flash-{cnt % 2}"
    return ""

st.markdown("""
<div style="margin-bottom: 16px;">
    <h1 style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin: 0;">
        ⚖️ Custom Pair Arbitrage <span style="background: linear-gradient(135deg, #D97706 0%, #B45309 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">& Lot Sizing Lab</span>
    </h1>
    <div style="color: #64748B; font-size: 0.88rem; font-weight: 500; margin-top: 4px;">
        Institutional statistical arbitrage spread analytics & physical weight delta neutrality
    </div>
</div>
""", unsafe_allow_html=True)

symbols = get_distinct_symbols()

if len(symbols) >= 2:
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        leg1 = st.selectbox("Select Leg 1 (Primary Contract)", symbols, index=0)
    with col_sel2:
        leg2 = st.selectbox("Select Leg 2 (Hedge Leg)", symbols, index=1 if len(symbols) > 1 else 0)
        
    if leg1 == leg2:
        st.warning("⚠️ Please select two distinct contracts to evaluate pair spread.")
    else:
        sql = f"""
            SELECT p1.trade_date, p1.close_pg as p1_close, p2.close_pg as p2_close,
                   (p1.close_pg - p2.close_pg) as spread_pg
            FROM prices_norm p1
            JOIN prices_norm p2 ON p1.trade_date = p2.trade_date
            WHERE p1.symbol = '{leg1}' AND p2.symbol = '{leg2}'
            ORDER BY p1.trade_date
        """
        df_pair = query_df(sql)
        
        if not df_pair.empty:
            latest_spread = df_pair.iloc[-1]["spread_pg"]
            mean_spread = df_pair["spread_pg"].mean()
            std_spread = df_pair["spread_pg"].std()
            z_score = (latest_spread - mean_spread) / std_spread if std_spread != 0 else 0.0
            
            flash_spread = get_change_flash_class("compare_spread", (leg1, leg2, round(latest_spread, 2)))
            flash_mean = get_change_flash_class("compare_mean", (leg1, leg2, round(mean_spread, 2)))
            flash_std = get_change_flash_class("compare_std", (leg1, leg2, round(std_spread, 2)))
            flash_z = get_change_flash_class("compare_z", (leg1, leg2, round(z_score, 2)))
            
            # 4 Metric Cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="bento-card bento-card-cyan-tint">
                    <div class="bento-label">CURRENT SPREAD</div>
                    <div class="bento-val"><span class="{flash_spread}">₹{latest_spread:+.2f}</span><span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                    <div style="font-size: 0.72rem; color: #64748B;">Latest pure basis gap</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="bento-card bento-card-slate-tint">
                    <div class="bento-label">HISTORICAL MEAN</div>
                    <div class="bento-val"><span class="{flash_mean}">₹{mean_spread:+.2f}</span><span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                    <div style="font-size: 0.72rem; color: #64748B;">Mean equilibrium price</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="bento-card bento-card-amber-tint">
                    <div class="bento-label">SPREAD VOLATILITY (1σ)</div>
                    <div class="bento-val"><span class="{flash_std}">₹{std_spread:.2f}</span><span style="font-size: 0.8rem; color:#64748B;">/g</span></div>
                    <div style="font-size: 0.72rem; color: #64748B;">Standard deviation</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                status_text = "OVERVALUED" if z_score > 1.5 else ("UNDERVALUED" if z_score < -1.5 else "FAIR VALUE")
                status_color = "#DC2626" if z_score > 1.5 else ("#059669" if z_score < -1.5 else "#64748B")
                st.markdown(f"""
                <div class="bento-card bento-card-purple-tint">
                    <div class="bento-label">Z-SCORE DEVIATION</div>
                    <div class="bento-val"><span class="{flash_z}">{z_score:+.2f}σ</span></div>
                    <div style="font-size: 0.75rem; font-weight: 700; color: {status_color};"><span class="{flash_z}">{status_text}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            # Pair Spread Chart
            st.markdown('<div class="bento-card bento-card-blue-tint" style="padding: 12px 18px;">', unsafe_allow_html=True)
            fig_spread = go.Figure()
            fig_spread.add_trace(go.Scatter(
                x=df_pair["trade_date"], 
                y=df_pair["spread_pg"], 
                name=f"{leg1} - {leg2} Spread",
                line=dict(color="#D97706", width=2.2)
            ))
            fig_spread.add_hline(y=mean_spread, line_dash="dash", line_color="#64748B", annotation_text="Mean")
            fig_spread.add_hline(y=mean_spread + 2 * std_spread, line_dash="dot", line_color="#DC2626", annotation_text="+2σ Upper Bound")
            fig_spread.add_hline(y=mean_spread - 2 * std_spread, line_dash="dot", line_color="#10B981", annotation_text="-2σ Lower Bound")
            
            fig_spread.update_layout(
                template="plotly_white",
                height=380,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248, 250, 252, 0.7)",
                xaxis=dict(gridcolor="rgba(226, 232, 240, 0.8)"),
                yaxis=dict(title="Spread (₹/g Pure Gold)", gridcolor="rgba(226, 232, 240, 0.8)")
            )
            st.plotly_chart(fig_spread, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Sizing & Friction Engine
            st.markdown('<div style="font-size: 1.1rem; font-weight: 800; color: #0F172A; margin: 14px 0 8px 0;">🧮 What-If Trade Sizing & Friction Analysis</div>', unsafe_allow_html=True)
            
            c_size1, c_size2 = st.columns(2)
            with c_size1:
                st.markdown('<div class="bento-card bento-card-amber-tint">', unsafe_allow_html=True)
                leg1_lots = st.number_input(f"Enter Lots for {leg1}", min_value=1, value=1)
                
                mult_map = {"GOLDM": 100, "GOLDTEN": 10, "GOLDGUINEA": 8, "GOLDPETAL": 1}
                g1 = mult_map.get(leg1, 10) * leg1_lots
                g2_needed = g1 / mult_map.get(leg2, 1)
                
                flash_g2 = get_change_flash_class("compare_g2", (leg1, leg2, round(g2_needed, 2)))
                flash_g1 = get_change_flash_class("compare_g1", (leg1, g1))
                
                st.markdown(f"""
                <div style="background: rgba(217, 119, 6, 0.08); border: 1px solid rgba(217, 119, 6, 0.3); border-radius: 12px; padding: 12px; margin-top: 10px;">
                    <div style="font-weight: 800; color: #92400E; font-size: 0.88rem;">💡 Delta-Neutral Hedge Requirement:</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 4px 0;">
                        Trade <span class="{flash_g2}"><strong>{g2_needed:.1f} lots</strong></span> of {leg2}
                    </div>
                    <div style="font-size: 0.75rem; color: #64748B;">
                        Equalizes physical gold weight at <span class="{flash_g1}"><strong>{g1:,} pure grams</strong></span>.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c_size2:
                st.markdown('<div class="bento-card bento-card-mint-tint">', unsafe_allow_html=True)
                cost_bp = estimate_roundtrip_cost_bp(20.0, 1, 75000.0)
                exp_edge_bp = abs(z_score * 15.0)
                net_edge = exp_edge_bp - cost_bp
                
                flash_cost = get_change_flash_class("compare_cost", round(cost_bp, 1))
                flash_edge = get_change_flash_class("compare_edge", round(net_edge, 1))
                
                st.markdown(f"""
                <div style="font-size: 0.75rem; font-weight: 800; color: #64748B; text-transform: uppercase;">NET EXPECTED ARBITRAGE EDGE</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: {'#059669' if net_edge > 0 else '#DC2626'}; font-family: 'JetBrains Mono', monospace; margin: 4px 0;">
                    <span class="{flash_edge}">{net_edge:+.1f} bp</span>
                </div>
                <div style="font-size: 0.78rem; color: #475569; margin-top: 6px;">
                    Gross Model Edge: <strong>+{exp_edge_bp:.1f} bp</strong> • Roundtrip Friction: <strong class="{flash_cost}">{cost_bp:.1f} bp</strong>
                </div>
                <div style="margin-top: 10px;">
                    {"<div style='background: #D1FAE5; color: #065F46; padding: 6px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 700;'>✅ Actionable Arbitrage Signal (Edge > Costs)</div>" if net_edge > 0 else "<div style='background: #FEE2E2; color: #991B1B; padding: 6px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 700;'>🛑 Filtered by Quiet Alert Gate (Unprofitable after fees)</div>"}
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No paired pricing records found in database.")
else:
    st.info("Insufficient contract symbols found in database. Run pipeline to populate.")