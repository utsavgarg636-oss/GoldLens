# 👑 GoldLens: Institutional MCX Gold Derivatives Relative Value & Arbitrage Desk

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-Embedded_OLAP-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![MCX India](https://img.shields.io/badge/Exchange-MCX_India-D97706?style=for-the-badge&logo=cashapp&logoColor=white)](https://www.mcxindia.com)
[![Status](https://img.shields.io/badge/Desk_Engine-Live_Production-10B981?style=for-the-badge)]()

**An institutional relative value (RV) trading engine, physical weight normalization desk, and microstructure friction-filtered arbitrage terminal for Multi Commodity Exchange of India (MCX) Gold derivatives.**

[Live Architecture](#-system-architecture) • [Core Problem & Solution](#-the-core-problem-goldlens-solves) • [Contract Matrix](#-mcx-contract-specifications) • [Quickstart Guide](#-quickstart--execution-guide) • [Demo Walkthrough](#-terminal-features--walkthrough)

</div>

---

## 📌 Executive Summary

India's Multi Commodity Exchange (MCX) lists four distinct gold futures contracts: **GOLDM**, **GOLDTEN**, **GOLDGUINEA**, and **GOLDPETAL**. While retail traders frequently assume these contracts trade synchronously, they actually differ fundamentally across:
1. **Contract Multipliers & Lot Sizes** (100g, 10g, 8g, 1g).
2. **Physical Fineness / Purity** (`0.995` for Gold Mini vs `0.999` for Gold Guinea, Petal, and Ten).
3. **Quotation Base Units** (Quoted in ₹ / 10g, ₹ / 8g, or ₹ / 1g).
4. **Market Microstructure Friction** (Exchange fees, CTT, GST, Stamp Duty, and bid-ask tick slippage).

These structural mismatches make direct price comparisons misleading. A raw spread that appears superficially profitable often turns negative once statutory levies are applied. Furthermore, naive 1-lot vs. 1-lot pair trades introduce catastrophic directional exposure because a single lot of GOLDM represents **100 pure grams**, whereas a lot of GOLDGUINEA represents only **8 grams**.

**GoldLens** bridges this gap. It normalizes all derivatives into an exact **₹ / gram Pure Gold basis**, fits spatial log-carry term structure curves, evaluates stationarity via Augmented Dickey-Fuller (ADF) tests, sizes trades for true physical delta-neutrality, and filters signals through a **Quiet Alert Gate** that only flags trades when theoretical alpha reliably exceeds real round-trip execution friction.

---

## 🔬 The Core Problem GoldLens Solves

```
                         ┌──────────────────────────────────────────┐
                         │      THE MCX RELATIVE VALUE DILEMMA      │
                         └────────────────────┬─────────────────────┘
                                              │
           ┌───────────────────────┬──────────┴──────────┬───────────────────────┐
           ▼                       ▼                     ▼                       ▼
  GOLDM (100g, 0.995)     GOLDTEN (10g, 0.999)  GOLDGUINEA (8g, 0.999)  GOLDPETAL (1g, 0.999)
     ₹74,461 / 10g           ₹74,773 / 10g          ₹59,816 / 8g             ₹7,476 / 1g
           │                       │                     │                       │
           └───────────────────────┴──────────┬──────────┴───────────────────────┘
                                              ▼
                           Raw Quotes Cannot Be Compared Directly!
                           • Mismatched Gram Weights (100g vs 10g vs 8g vs 1g)
                           • Purity Divergence (0.995 Fineness vs 0.999 Fineness)
                           • Sizing Asymmetry (1 Lot GOLDM ≠ 1 Lot GOLDGUINEA)
                           • Statutory Tax Drag (0.01% CTT, 18% GST, Stamp Duty)
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │  ⚡ GOLDLENS ENGINE SOLUTION  │
                              └───────────────┬───────────────┘
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
            [1. PURE BASIS GAP]      [2. DELTA-NEUTRALITY]   [3. QUIET ALERT GATE]
            ₹ / Pure Gram Basis     Exact Weight Equalizer   Alpha > All Statutory
            (e.g., ₹7,483.49/g)      (1 Lot = 12.5 Lots)     Taxes & Tick Slippage
```

---

## 📊 MCX Contract Specifications

GoldLens normalizes contracts according to the official MCX India contract specifications:

| Contract Code | Unit Name | Physical Lot Size | Purity / Fineness | Quoted Basis | Pure Weight / Lot | Sizing Ratio vs GOLDM |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`GOLDM`** | Gold Mini | 100 grams | **0.995** (99.5%) | ₹ / 10 grams | **99.50 grams** | **1.00 Lot (Anchor)** |
| **`GOLDTEN`** | Gold Ten | 10 grams | **0.999** (99.9%) | ₹ / 10 grams | **9.99 grams** | **~9.96 Lots** |
| **`GOLDGUINEA`**| Gold Guinea | 8 grams | **0.999** (99.9%) | ₹ / 8 grams | **7.992 grams** | **~12.45 Lots** |
| **`GOLDPETAL`** | Gold Petal | 1 gram | **0.999** (99.9%) | ₹ / 1 gram | **0.999 grams** | **~99.60 Lots** |

### Mathematical Normalization Formula
$$\text{Basis}_{\text{pure}} = \frac{\text{Raw Quote}}{\text{Quoted Grams} \times \text{Fineness}}$$

---

## ⚡ Key Innovations & Features

### 1. 🎛️ Spatial Relative Value & Term Structure Centerstage
- Computes real-time pure gold price deviation ($\text{Basis}_{i} - \text{Benchmark}$).
- Fits a spatial log-carry regression curve across maturities to detect rich/cheap anomalies.
- Calculates rolling 60-day rolling Z-Score residuals ($Z = \frac{\text{Spread} - \mu}{\sigma}$) to detect $\pm 2\sigma$ statistical extremes.

### 2. 💡 Delta-Neutral Order Ticket & Sizing Engine
- Solves the physical mismatch problem by computing the precise hedge ratio:
  $$\text{Required Hedge Lots} = \frac{\text{Lots}_{\text{leg1}} \times \text{Grams}_{\text{leg1}}}{\text{Grams}_{\text{leg2}}}$$
- Prevents traders from holding unintended net-directional commodity risk during pair trades.

### 3. 🛡️ Quiet Alert Gate & Statutory Microstructure Simulator
- Evaluates real Indian statutory friction before signaling any trade:
  - **Commodity Transaction Tax (CTT)**: $0.010\%$ on sell side notional.
  - **Exchange Turnover / Brokerage**: Configurable ₹ per executed order.
  - **GST**: $18\%$ on brokerage fees.
  - **Stamp Duty**: $0.003\%$ state tax.
  - **Tick Slippage Buffer**: $0.50$ ₹/tick market depth impact.
- **Quiet Gate Filter**:
  $$\text{Net Edge} = \text{Model Gross Edge (bp)} - \text{Roundtrip Statutory Cost (bp)}$$
  Only generates an alert if $\text{Net Edge} > 0$ and $\text{Gross Edge} \ge \text{Threshold}$.

### 4. 📈 Walk-Forward Backtester with Strict $t+1$ Fills
- Simulates historical statistical arbitrage equity curves with **zero look-ahead bias**.
- Enforces strict next-day open fills ($t+1$).
- Calculates annualized Sharpe Ratio, Sortino Ratio, Peak-to-Trough Maximum Drawdown, Win Rate, and Profit Factor.

### 5. ✨ Dynamic 8-Style UI Fusion & Single-Flash Feedback
- **Delicate Ambient Mesh Gradients**: Curated pastel tints across tabs (Champagne Gold, Sapphire Blue, Emerald Mint, Terracotta Peach).
- **Single-Flash Visual Telemetry**: Automatically detects when any input changes and highlights the updated output value once for $1.2$ seconds before smoothly settling back to normal.

---

## 📂 System Architecture

```
GoldLens/
├── app/
│   ├── 🏠_Home.py               # Main 4-Tab Analytical Dashboard & Cockpit
│   └── pages/
│       ├── 1_⚖️_Compare.py       # Custom Pair Arbitrage & Sizing Desk
│       └── 2_📊_Backtest.py      # Walk-Forward Backtest Attribution & Risk Desk
├── data/
│   ├── raw/                     # Historical JSON daily contract bhavcopies
│   └── processed/
│       └── goldlens.duckdb      # Embedded DuckDB high-performance OLAP database
├── src/
│   └── goldlens/
│       ├── __init__.py
│       ├── ingest.py            # Data ingestion & multi-contract pipeline
│       ├── store.py             # Schema definition & DuckDB table loader
│       ├── normalize.py         # Pure basis conversion (₹/g Pure Gold)
│       ├── curve.py             # Term structure carry regression & Z-Scores
│       ├── validate.py          # Data hygiene, anomaly & duplicate handling
│       ├── relval.py            # Stationarity & Augmented Dickey-Fuller tests
│       ├── costs.py             # Indian statutory tax & friction engine
│       ├── signals.py           # Z-Score mean-reversion signal generator
│       ├── alerts.py            # Quiet Alert Gate friction filter
│       └── backtest.py          # Walk-forward simulation engine (t+1 execution)
├── tests/
│   ├── conftest.py              # Pytest fixtures and mock environments
│   ├── test_normalize.py        # Normalization mathematical proofs
│   └── test_validation.py       # Data integrity & schema validations
├── config.yaml                  # Global parameters, thresholds & friction rates
├── specs.yaml                   # MCX contract fineness and multiplier specs
├── requirements.txt             # Locked project dependencies
└── README.md                    # Institutional terminal documentation
```

---

## 🚀 Quickstart & Execution Guide

### Step 1: Environment Setup
```powershell
# Clone the repository
git clone https://github.com/utsavgarg636-oss/GoldLens.git
cd GoldLens

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt
```

### Step 2: Run End-to-End Quantitative Pipeline
```powershell
# Ingest historical data and load DuckDB
python -m src.goldlens.ingest
python -m src.goldlens.store

# Run pure basis normalization and curve fitting
python -m src.goldlens.normalize
python -m src.goldlens.curve

# Execute walk-forward strategy backtest
python -m src.goldlens.backtest
```

### Step 3: Run Test Suite
```powershell
python -m pytest tests/ -v
```

### Step 4: Launch the Live Dashboard
```powershell
streamlit run "app/🏠_Home.py"
```
*Navigate to `http://localhost:8501` in your browser.*

---

## 🖥️ Terminal Features & Walkthrough

| Tab / Page | Core Focus | Key Institutional Capabilities |
| :--- | :--- | :--- |
| **👑 Terminal Cockpit** | Spatial Term Structure & Opportunity Feed | Multi-contract basis cards, Carry regression scatter plot, Z-score correlation matrix, and Quiet Alert Gate opportunity feed. |
| **⚖️ Pair Arbitrage Lab** | Pair Analytics & Delta Sizing | Custom pair selection, rolling spread bands ($\pm 2\sigma$), ADF test stationarity status, and exact weight delta-neutral lot calculator. |
| **📊 Backtest & Risk Engine** | Walk-Forward Quantitative Attribution | Cumulative net P&L equity curve (bp), monthly returns heatmap, Sharpe ratio, Sortino ratio, max drawdown, and win rate. |
| **🧮 Friction Simulator** | Market Microstructure Analysis | Interactive statutory tax calculator (Brokerage, GST, CTT, Stamp Duty, Slippage) and net basis point drag simulation. |

---

## ⚖️ License & Disclaimer

This project is licensed under the **MIT License**.

> **Disclaimer**: *GoldLens is designed for institutional quantitative research and financial engineering demonstration purposes. Commodity derivatives trading on MCX involves substantial financial risk. Past statistical mean reversion is not indicative of future performance.*