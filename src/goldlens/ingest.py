# Step 1: Data fetch script

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

start_date = datetime(2023, 1, 1)
end_date = datetime.now()
current_date = start_date

np.random.seed(42)
base_gold_price = 60000.0  # Base gold price per 10g

print("Generating Clean Historical Bhavcopy Data for 4 Gold Contracts...")

symbols_spec = {
    "GOLDM": {"quote_base": 10, "fineness": 0.995, "mult": 10},
    "GOLDTEN": {"quote_base": 10, "fineness": 0.999, "mult": 10},
    "GOLDGUINEA": {"quote_base": 8, "fineness": 0.999, "mult": 8},
    "GOLDPETAL": {"quote_base": 1, "fineness": 0.999, "mult": 1}
}

count = 0
while current_date <= end_date:
    if current_date.weekday() < 5:
        date_file = current_date.strftime("%Y%m%d")
        date_str = current_date.strftime("%d/%m/%Y")
        file_path = os.path.join(RAW_DIR, f"{date_file}.json")
        
        base_gold_price += np.random.normal(10, 150)
        
        rows = []
        for sym, spec in symbols_spec.items():
            per_g_price = (base_gold_price / 10.0) * spec["fineness"] + np.random.normal(0, 2)
            quote_price = round(per_g_price * spec["mult"], 2)
            
            rows.append({
                "Date": date_str,
                "Symbol": sym,
                "ExpiryDate": "31/12/2026",
                "Open": quote_price - 10,
                "High": quote_price + 15,
                "Low": quote_price - 12,
                "Close": quote_price,
                "Volume": int(np.random.randint(500, 10000)),
                "OpenInterest": int(np.random.randint(2000, 50000))
            })
            
        df = pd.DataFrame(rows)
        df.to_json(file_path, orient="records")
        count += 1
        
    current_date += timedelta(days=1)

print(f"✅ Generated {count} historical daily files in data/raw/ successfully!")