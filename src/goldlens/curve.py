# Step 3: Curve fitting & residuals

import duckdb
import numpy as np
import pandas as pd

def run_curve_analytics():
    db_path = "data/processed/goldlens.duckdb"
    conn = duckdb.connect(db_path)
    
    df = conn.execute("SELECT * FROM prices_norm ORDER BY trade_date").fetchdf()
    
    if df.empty:
        print("❌ Normalized data nahi mila!")
        return

    # Daily Curve Fit Logic
    processed_days = []
    for t_date, group in df.groupby("trade_date"):
        day = group.copy()
        if len(day) >= 3 and not day["close_pg"].isnull().any():
            x = day["dte"].values.astype(float)
            y = np.log(day["close_pg"].values)
            w = np.sqrt(day["oi"].values + 1)
            
            b, a = np.polyfit(x, y, 1, w=w) # b = daily log carry
            
            day["resid_bp"] = (y - (a + b * x)) * 1e4
            day["implied_carry_ann"] = b * 365
        else:
            day["resid_bp"] = 0.0
            day["implied_carry_ann"] = 0.0
            
        processed_days.append(day)
        
    final_df = pd.concat(processed_days, ignore_index=True)
    
    # 60-Day Rolling Z-Score (No Look-Ahead)
    final_df["rolling_mean"] = final_df.groupby("symbol")["resid_bp"].transform(
        lambda x: x.rolling(60, min_periods=10).mean()
    )
    final_df["rolling_std"] = final_df.groupby("symbol")["resid_bp"].transform(
        lambda x: x.rolling(60, min_periods=10).std()
    )
    final_df["z_score"] = (final_df["resid_bp"] - final_df["rolling_mean"]) / (final_df["rolling_std"] + 1e-6)
    
    # DuckDB Table Mein Save Karo
    conn.execute("DROP TABLE IF EXISTS rv_daily")
    conn.register("temp_rv", final_df[["trade_date", "symbol", "expiry_date", "close_pg", "resid_bp", "implied_carry_ann", "z_score", "is_thin"]])
    conn.execute("CREATE TABLE rv_daily AS SELECT * FROM temp_rv")
    
    print("✅ Analytics Engine Complete! Curve residuals aur Z-Scores rv_daily table mein save ho gaye.")
    conn.close()

if __name__ == "__main__":
    run_curve_analytics()