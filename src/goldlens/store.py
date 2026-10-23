# DuckDB storage handler

import os
import glob
import json
import pandas as pd
import duckdb

# Database directory setup
db_dir = "data/processed"
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "goldlens.duckdb")

# DuckDB connection
conn = duckdb.connect(db_path)

# raw_bhavcopy table create karo
conn.execute("""
CREATE TABLE IF NOT EXISTS raw_bhavcopy (
    trade_date DATE,
    symbol VARCHAR,
    expiry_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    oi BIGINT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("DuckDB Connection Ready. Processing JSON files from data/raw...")

raw_files = glob.glob("data/raw/*.json")
gold_symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]

inserted_rows = 0

for file_path in raw_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        df = pd.DataFrame(data)
        if df.empty:
            continue
            
        df.columns = [c.strip().lower() for c in df.columns]
        
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
            df_gold = df[df["symbol"].isin(gold_symbols)].copy()
            
            if not df_gold.empty:
                mapped_df = pd.DataFrame()
                mapped_df["trade_date"] = pd.to_datetime(df_gold["date"], format="%d/%m/%Y", errors="coerce")
                mapped_df["symbol"] = df_gold["symbol"]
                mapped_df["expiry_date"] = pd.to_datetime(df_gold["expirydate"], format="%d/%m/%Y", errors="coerce")
                mapped_df["open"] = pd.to_numeric(df_gold["open"], errors="coerce")
                mapped_df["high"] = pd.to_numeric(df_gold["high"], errors="coerce")
                mapped_df["low"] = pd.to_numeric(df_gold["low"], errors="coerce")
                mapped_df["close"] = pd.to_numeric(df_gold["close"], errors="coerce")
                mapped_df["volume"] = pd.to_numeric(df_gold["volume"], errors="coerce").fillna(0)
                mapped_df["oi"] = pd.to_numeric(df_gold["openinterest"], errors="coerce").fillna(0)
                
                conn.register("temp_df", mapped_df)
                conn.execute("""
                    INSERT INTO raw_bhavcopy 
                    SELECT trade_date, symbol, expiry_date, open, high, low, close, volume, oi, CURRENT_TIMESTAMP 
                    FROM temp_df
                """)
                inserted_rows += len(mapped_df)
    except Exception as e:
        continue

print(f"✅ Success! Total {inserted_rows} rows loaded into data/processed/goldlens.duckdb")
conn.close()