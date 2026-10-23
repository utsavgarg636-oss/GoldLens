# Step 3: Z-scores & stationarity

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

def test_stationarity(series: pd.Series) -> float:
    """
    ADF Test to check if the residual series is stationary/mean-reverting.
    """
    clean_series = series.dropna()
    if len(clean_series) < 20:
        return 1.0  # Not stationary
    
    res = adfuller(clean_series)
    return res[1]  # p-value