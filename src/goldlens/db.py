# Thread-safe cached DuckDB connector and query helpers for GoldLens

import os
import sys
import duckdb
import pandas as pd

# Guarantee workspace root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "goldlens.duckdb")

def get_db_path() -> str:
    return DB_PATH

def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """
    Returns a thread-safe connection to the DuckDB database.
    Defaults to read_only=True to prevent concurrent write locks.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DuckDB database not found at {DB_PATH}.")
    return duckdb.connect(DB_PATH, read_only=read_only)

def query_df(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Executes a read-only SQL query and returns a pandas DataFrame.
    Guarantees connection cleanup.
    """
    conn = get_connection(read_only=True)
    try:
        if params:
            df = conn.execute(sql, params).fetchdf()
        else:
            df = conn.execute(sql).fetchdf()
        return df
    finally:
        conn.close()

def get_latest_prices() -> pd.DataFrame:
    sql = """
        SELECT symbol, close_pg, close, trade_date, volume, oi, dte
        FROM prices_norm 
        WHERE trade_date = (SELECT MAX(trade_date) FROM prices_norm)
        ORDER BY symbol
    """
    try:
        return query_df(sql)
    except Exception:
        return pd.DataFrame()

def get_all_normalized_prices() -> pd.DataFrame:
    sql = "SELECT trade_date, symbol, close_pg, close, dte, oi, volume FROM prices_norm ORDER BY trade_date"
    try:
        return query_df(sql)
    except Exception:
        return pd.DataFrame()

def get_latest_rv_residuals() -> pd.DataFrame:
    sql = """
        SELECT trade_date, symbol, close_pg, close, resid_bp, implied_carry_ann, z_score, dte, oi, volume
        FROM rv_daily
        WHERE trade_date = (SELECT MAX(trade_date) FROM rv_daily)
        ORDER BY symbol
    """
    try:
        return query_df(sql)
    except Exception:
        return pd.DataFrame()

def get_all_rv_data() -> pd.DataFrame:
    sql = "SELECT trade_date, symbol, close_pg, resid_bp, implied_carry_ann, z_score FROM rv_daily ORDER BY trade_date"
    try:
        return query_df(sql)
    except Exception:
        return pd.DataFrame()

def get_distinct_symbols() -> list:
    sql = "SELECT DISTINCT symbol FROM prices_norm ORDER BY symbol"
    try:
        df = query_df(sql)
        return df["symbol"].tolist() if not df.empty else []
    except Exception:
        return ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]

def get_backtest_pnl() -> pd.DataFrame:
    sql = "SELECT trade_date, symbol, position, pnl FROM pnl_daily ORDER BY trade_date"
    try:
        return query_df(sql)
    except Exception:
        return pd.DataFrame()
