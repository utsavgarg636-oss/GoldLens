# Step 4: Walk-forward backtest loop

import os
import sys
import duckdb
import pandas as pd

# Guarantee workspace root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_backtest_replay():
    """
    Walk-forward backtest replay simulation with t+1 fills per contract symbol.
    """
    db_path = os.path.join(PROJECT_ROOT, "data", "processed", "goldlens.duckdb")
    conn = duckdb.connect(db_path)
    
    df = conn.execute("SELECT * FROM rv_daily ORDER BY symbol, trade_date").fetchdf()
    
    if df.empty:
        print("[!] Backtest: No data found.")
        conn.close()
        return

    df["signal"] = df["z_score"].apply(lambda z: 1 if z <= -2.0 else (-1 if z >= 2.0 else 0))
    # Ensure t+1 fill shift is grouped by symbol to avoid cross-symbol contamination
    df["position"] = df.groupby("symbol")["signal"].shift(1).fillna(0)
    df["pnl"] = df["position"] * df["resid_bp"]
    
    conn.execute("DROP TABLE IF EXISTS pnl_daily")
    conn.register("temp_pnl", df)
    
    conn.execute("CREATE TABLE pnl_daily AS SELECT trade_date, symbol, position, pnl FROM temp_pnl ORDER BY trade_date, symbol")
    
    print("[OK] Walk-forward Backtest Replay Complete!")
    conn.close()

if __name__ == "__main__":
    run_backtest_replay()