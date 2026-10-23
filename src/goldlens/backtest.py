# Step 4: Walk-forward backtest loop

import duckdb
import pandas as pd

def run_backtest_replay():
    """
    Walk-forward backtest replay simulation with t+1 fills.
    """
    db_path = "data/processed/goldlens.duckdb"
    conn = duckdb.connect(db_path)
    
    df = conn.execute("SELECT * FROM rv_daily ORDER BY trade_date").fetchdf()
    
    if df.empty:
        print("❌ Backtest: No data found.")
        conn.close()
        return

    df["signal"] = df["z_score"].apply(lambda z: 1 if z <= -2.0 else (-1 if z >= 2.0 else 0))
    df["position"] = df["signal"].shift(1).fillna(0)  # t+1 fill execution (No Look-ahead)
    df["pnl"] = df["position"] * df["resid_bp"]
    
    conn.execute("DROP TABLE IF EXISTS pnl_daily")
    conn.register("temp_pnl", df)
    
    # Query updated to match registered dataframe name temp_pnl
    conn.execute("CREATE TABLE pnl_daily AS SELECT trade_date, symbol, position, pnl FROM temp_pnl")
    
    print("✅ Walk-forward Backtest Replay Complete!")
    conn.close()

if __name__ == "__main__":
    run_backtest_replay()