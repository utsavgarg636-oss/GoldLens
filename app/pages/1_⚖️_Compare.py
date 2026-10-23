import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
from src.goldlens.costs import estimate_roundtrip_cost_bp

st.set_page_config(page_title="GoldLens | Pair Arbitrage Calculator", page_icon="⚖️", layout="wide")

st.title("⚖️ Custom Pair Arbitrage & Lot Size Calculator")
st.caption("Evaluate real-time statistical arbitrage spread between any two MCX Gold contracts.")

db_path = "data/processed/goldlens.duckdb"
conn = duckdb.connect(db_path)

try:
    df_prices = conn.execute("SELECT DISTINCT symbol FROM prices_norm").fetchdf()
    symbols = df_prices['symbol'].tolist()
    
    if len(symbols) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            leg1 = st.selectbox("Select Leg 1 (Long/Short)", symbols, index=0)
        with col2:
            leg2 = st.selectbox("Select Leg 2 (Hedge Leg)", symbols, index=1 if len(symbols)>1 else 0)
            
        if leg1 == leg2:
            st.warning("Please select two different contracts to calculate arbitrage spread.")
        else:
            # Query price data for selected pair
            query = f"""
                SELECT p1.trade_date, p1.close_pg as p1_close, p2.close_pg as p2_close,
                       (p1.close_pg - p2.close_pg) as spread_pg
                FROM prices_norm p1
                JOIN prices_norm p2 ON p1.trade_date = p2.trade_date
                WHERE p1.symbol = '{leg1}' AND p2.symbol = '{leg2}'
                ORDER BY p1.trade_date
            """
            df_pair = conn.execute(query).fetchdf()
            
            if not df_pair.empty:
                latest_spread = df_pair.iloc[-1]['spread_pg']
                mean_spread = df_pair['spread_pg'].mean()
                std_spread = df_pair['spread_pg'].std()
                z_score = (latest_spread - mean_spread) / std_spread if std_spread != 0 else 0.0
                
                # Top Metrics Display
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current Per-Gram Spread", f"₹{latest_spread:.2f}/g")
                m2.metric("Mean Historical Spread", f"₹{mean_spread:.2f}/g")
                m3.metric("Spread Volatility (StdDev)", f"₹{std_spread:.2f}/g")
                m4.metric("Current Z-Score Deviation", f"{z_score:.2f} σ", 
                          delta="Overvalued" if z_score > 1.5 else ("Undervalued" if z_score < -1.5 else "Fair Value"),
                          delta_color="inverse" if z_score > 1.5 else "normal")
                
                st.markdown("---")
                
                # Pair Spread Chart
                fig_pair = go.Figure()
                fig_pair.add_trace(go.Scatter(x=df_pair['trade_date'], y=df_pair['spread_pg'], name=f"{leg1} - {leg2} Spread", line=dict(color="#FFD700", width=2)))
                fig_pair.add_hline(y=mean_spread, line_dash="dash", line_color="#8A8F9E", annotation_text="Mean")
                fig_pair.add_hline(y=mean_spread + 2*std_spread, line_dash="dot", line_color="#FF5252", annotation_text="+2σ Upper Bound")
                fig_pair.add_hline(y=mean_spread - 2*std_spread, line_dash="dot", line_color="#00E676", annotation_text="-2σ Lower Bound")
                
                fig_pair.update_layout(template="plotly_dark", height=400, title=f"Historical Price Spread ({leg1} vs {leg2})")
                st.plotly_chart(fig_pair, use_container_width=True)
                
                # Lot Ratio & Sizing Engine
                st.subheader("🧮 What-If Trade Sizing & Friction Analysis")
                c1, c2 = st.columns(2)
                with c1:
                    leg1_lots = st.number_input(f"Lots for {leg1}", min_value=1, value=1)
                    # Contract multipliers approx
                    multiplier_map = {"GOLDM": 100, "GOLDTEN": 10, "GOLDGUINEA": 8, "GOLDPETAL": 1}
                    g1 = multiplier_map.get(leg1, 10) * leg1_lots
                    g2_needed = g1 / multiplier_map.get(leg2, 1)
                    st.info(f"💡 Equivalent Hedge: Trade **{round(g2_needed, 1)}** lots of **{leg2}** to achieve delta neutrality ({g1} grams pure gold).")
                
                with c2:
                    cost_bp = estimate_roundtrip_cost_bp(20.0, 1, 75000.0)
                    expected_edge_bp = abs(z_score * 15.0)  # estimated edge in bp
                    net_edge = expected_edge_bp - cost_bp
                    
                    st.write(f"**Estimated Gross Edge:** `{expected_edge_bp:.1f} bp`")
                    st.write(f"**Total Roundtrip Friction:** `{cost_bp:.1f} bp`")
                    if net_edge > 0:
                        st.success(f"✅ **Actionable Signal:** Net Edge after Costs = `+{net_edge:.1f} bp`")
                    else:
                        st.error(f"🛑 **Quiet Alert:** Signal Filtered. Net Edge after Costs = `{net_edge:.1f} bp` (Unprofitable)")

except Exception as e:
    st.info("Run database pipeline first.")

conn.close()