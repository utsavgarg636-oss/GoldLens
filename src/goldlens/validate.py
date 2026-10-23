# Step 1: Data cleaning checks

import pandas as pd

def validate_bhavcopy_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Data quality checks: removes duplicate holiday rows & space-padded symbols.
    """
    if df.empty:
        return df
    
    df = df.copy()
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        
    df = df.drop_duplicates(subset=["trade_date", "symbol", "expiry_date"])
    return df