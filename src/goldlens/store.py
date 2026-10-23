# DuckDB storage handler

import os
import glob
import json
import sys
import pandas as pd
import duckdb

# Guarantee workspace root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.goldlens.validate import validate_bhavcopy_data

def run_store():
    # Database directory setup
    db_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "goldlens.duckdb")

    conn = duckdb.connect(db_path)

    print("DuckDB Connection Ready. Processing JSON files from data/raw...")

    raw_files = glob.glob(os.path.join(PROJECT_ROOT, "data", "raw", "*.json"))
    gold_symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]

    all_rows = []

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
                    
                    all_rows.append(mapped_df)
        except Exception:
            continue

    if all_rows:
        combined_df = pd.concat(all_rows, ignore_index=True)
        # Deduplicate using validate_bhavcopy_data
        combined_df = validate_bhavcopy_data(combined_df)
        combined_df = combined_df.sort_values(by=["trade_date", "symbol"]).reset_index(drop=True)
        
        conn.execute("DROP TABLE IF EXISTS raw_bhavcopy")
        conn.execute("""
        CREATE TABLE raw_bhavcopy (
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
        
        conn.register("temp_df", combined_df)
        conn.execute("""
            INSERT INTO raw_bhavcopy 
            SELECT trade_date, symbol, expiry_date, open, high, low, close, volume, oi, CURRENT_TIMESTAMP 
            FROM temp_df
        """)
        print(f"[OK] Success! Total {len(combined_df)} deduplicated rows loaded into raw_bhavcopy.")
    else:
        print("[!] No raw files processed.")

    conn.close()

if __name__ == "__main__":
    run_store()