# Step 4: Taxes & brokerage calculation

def calculate_transaction_costs(trade_value: float, is_sell: bool, config: dict) -> float:
    """
    Calculates Brokerage, CTT, GST, Stamp duty & Slippage.
    """
    costs = config.get("costs", {})
    brokerage = costs.get("brokerage_per_order_inr", 20.0)
    gst = brokerage * costs.get("gst_rate", 0.18)
    
    ctt = trade_value * costs.get("ctt_rate", 0.0001) if is_sell else 0.0
    stamp_duty = trade_value * costs.get("stamp_duty_rate", 0.00003) if not is_sell else 0.0
    
    return round(brokerage + gst + ctt + stamp_duty, 2)