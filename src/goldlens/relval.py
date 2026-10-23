# Step 3: Z-scores & stationarity

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

def test_stationarity(series: pd.Series) -> float:
    """ADF Test to check stationarity of residual series."""
    clean_series = series.dropna()
    if len(clean_series) < 20:
        return 1.0
    res = adfuller(clean_series)
    return res[1]

def calculate_performance_metrics(pnl_series: pd.Series, risk_free_rate: float = 0.06) -> dict:
    """
    Computes Wall-Street level performance & risk metrics:
    Sharpe Ratio, Sortino Ratio, Max Drawdown, Win Rate, and Profit Factor.
    """
    clean_pnl = pnl_series.fillna(0)
    if len(clean_pnl) == 0 or clean_pnl.std() == 0:
        return {
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown_bp": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "total_pnl_bp": 0.0
        }
    
    total_pnl = clean_pnl.sum()
    daily_mean = clean_pnl.mean()
    daily_std = clean_pnl.std()
    
    # Sharpe Ratio (Annualized)
    sharpe = (daily_mean * np.sqrt(252)) / daily_std if daily_std != 0 else 0.0
    
    # Downside Volatility for Sortino Ratio
    negative_returns = clean_pnl[clean_pnl < 0]
    downside_std = negative_returns.std() if len(negative_returns) > 0 else 1e-6
    sortino = (daily_mean * np.sqrt(252)) / downside_std if downside_std != 0 else 0.0
    
    # Max Drawdown Calculation
    cum_pnl = clean_pnl.cumsum()
    running_max = np.maximum.accumulate(cum_pnl)
    drawdown = cum_pnl - running_max
    max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0.0
    
    # Win Rate & Profit Factor
    winning_trades = clean_pnl[clean_pnl > 0]
    losing_trades = clean_pnl[clean_pnl < 0]
    
    win_rate = (len(winning_trades) / len(clean_pnl[clean_pnl != 0]) * 100) if len(clean_pnl[clean_pnl != 0]) > 0 else 0.0
    gross_profit = winning_trades.sum()
    gross_loss = abs(losing_trades.sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else (gross_profit if gross_profit > 0 else 0.0)
    
    return {
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "max_drawdown_bp": round(max_drawdown, 2),
        "win_rate_pct": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "total_pnl_bp": round(total_pnl, 2)
    }