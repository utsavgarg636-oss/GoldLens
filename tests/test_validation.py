from src.goldlens.validate import validate_bhavcopy_data
import pandas as pd

def test_data_validation():
    sample_df = pd.DataFrame([
        {"trade_date": "2026-10-22", "symbol": " GOLDM ", "expiry_date": "2026-11-05"},
        {"trade_date": "2026-10-22", "symbol": "GOLDM", "expiry_date": "2026-11-05"}
    ])
    
    cleaned = validate_bhavcopy_data(sample_df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["symbol"] == "GOLDM"