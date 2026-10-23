# 🏆 GoldLens: MCX Commodity Derivatives Intelligence & Relative Value Analytics

GoldLens is a robust, modular, and production-ready financial analytics engine designed for relative value (RV) trading, contract normalization, curve fitting, and walk-forward backtesting across MCX Gold derivatives (GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL).

---

## 📌 Features & Architecture Overview

* **Multi-Contract Normalization**: Converts all MCX gold quote units into a uniform basis (₹ / gram pure gold). Normalizes across fineness differences (0.995 vs 0.999) and quoted contract sizes (10g, 8g, 1g).
* **Curve Fitting & RV Mispricing**: Performs daily log-price curve regression against Days to Expiry (DTE). Computes open-interest weighted residuals and 60-day rolling Z-Scores without look-ahead bias.
* **Quiet Alert Gate Filter**: Prevents false signals by requiring expected edge (bp) to exceed round-trip transaction costs + slippage threshold.
* **Walk-Forward Strategy Backtest Replay**: Simulates trading strategy replay with t+1 execution fills (ensuring zero look-ahead bias).
* **DuckDB Analytics Engine**: High-performance embedded SQL database storage (`data/processed/goldlens.duckdb`) for fast querying and Streamlit UI rendering.

---

## 📂 Complete Project File Structure

GoldLens/
├── app/
│   ├── Home.py                  # Main Streamlit Dashboard
│   └── pages/
│       ├── 1_Compare.py         # Multi-contract overlay comparison
│       └── 2_Backtest.py        # Strategy P&L Equity curve
├── data/
│   ├── raw/                     # Historical JSON bhavcopies
│   └── processed/
│       └── goldlens.duckdb      # DuckDB database storage
├── src/
│   └── goldlens/
│       ├── __init__.py
│       ├── ingest.py            # Data fetcher & historical generator
│       ├── store.py             # DuckDB schema & raw data loader
│       ├── normalize.py         # Per-gram pure gold conversion logic
│       ├── curve.py             # Log-carry curve fitting & rolling Z-score
│       ├── validate.py          # Data cleaning & duplicate handling
│       ├── relval.py            # Stationarity & ADF tests
│       ├── costs.py             # Brokerage, CTT, GST & Slippage engine
│       ├── signals.py           # Long/Short pair signal generator
│       ├── alerts.py            # Quiet alert gate filter
│       └── backtest.py          # Walk-forward backtest replay simulator
├── tests/
│   ├── conftest.py              # Pytest path configurations
│   ├── test_normalize.py        # Normalization math unit tests
│   └── test_validation.py       # Data validation unit tests
├── config.yaml                  # System configuration parameters
├── specs.yaml                   # Contract multiplier & fineness specs
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation

---

## 🚀 Quickstart & Execution Guide for Teammates

### Step 1: Setup Environment
git clone [https://github.com/utsavgarg636-oss/GoldLens.git](https://github.com/utsavgarg636-oss/GoldLens.git)
cd GoldLens
.\venv\Scripts\activate
pip install -r requirements.txt

### Step 2: Run Data & Analytics Pipeline
python -m src.goldlens.ingest
python -m src.goldlens.store
python -m src.goldlens.normalize
python -m src.goldlens.curve
python -m src.goldlens.backtest

### Step 3: Run Unit Tests
python -m pytest

### Step 4: Launch Local Streamlit Web Application
streamlit run app/Home.py