# Step 2: Per-gram unit conversion

import os
import duckdb
import pandas as pd
import yaml

# Fallback specifications if specs.yaml is missing/empty
DEFAULT_SPECS = {
    "GOLDM": {"trading_unit_grams": 100, "quoted_unit_grams": 10, "fineness": 0.995, "tick_size": 1.0},
    "GOLDTEN": {"trading_unit_grams": 10, "quoted_unit_grams": 10, "fineness": 0.999, "tick_size": 1.0},
    "GOLDGUINEA": {"trading_unit_grams": 8, "quoted_unit_grams": 8, "fineness": 0.999, "tick_size": 1.0},
    "GOLDPETAL": {"trading_unit_grams": 1, "quoted_unit_grams": 1, "fineness": 0.999, "tick_size": 1.0}
}

def load_specs(specs_path="specs.yaml"):
    if os.path.exists(specs_path):
        try:
            with open(specs_path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    return loaded
        except Exception:
            pass
    return DEFAULT_SPECS

def run_normalization():
    db_path = "data/processed/goldlens.duckdb"
    if not os.path.exists(db_path):
        print("❌ DuckDB file nahi mili! Pehle store.py chalao.")
        return
        
    conn = duckdb.connect(db_path)
    df = conn.execute("SELECT * FROM raw_bhavcopy").fetchdf()
    
    if df.empty:
        print("❌ DuckDB mein koi raw data nahi mila!")
        conn.close()
        return

    specs = load_specs()
    
    # Per-gram pure gold conversion formula
    def get_price_pg(row):
        sym = str(row["symbol"]).strip().upper()
        if specs and sym in specs:
            spec = specs[sym]
            return round(row["close"] / spec["quoted_unit_grams"] / spec["fineness"], 4)
        return None

    df["close_pg"] = df.apply(get_price_pg, axis=1)
    
    # Dates & DTE calculation
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])
    df["dte"] = (df["expiry_date"] - df["trade_date"]).dt.days
    df["is_thin"] = df["volume"] < 100

    # DuckDB normalized table save
    conn.execute("DROP TABLE IF EXISTS prices_norm")
    conn.execute("""
    CREATE TABLE prices_norm (
        trade_date DATE,
        symbol VARCHAR,
        expiry_date DATE,
        dte INT,
        close_pg DOUBLE,
        volume BIGINT,
        oi BIGINT,
        is_thin BOOLEAN
    )
    """)
    
    conn.register("temp_norm", df[["trade_date", "symbol", "expiry_date", "dte", "close_pg", "volume", "oi", "is_thin"]])
    conn.execute("INSERT INTO prices_norm SELECT * FROM temp_norm")
    
    print(f"✅ Normalization Complete! {len(df)} rows converted to ₹/gram pure gold in DuckDB.")
    conn.close()

if __name__ == "__main__":
    run_normalization()