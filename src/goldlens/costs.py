# Step 4: Taxes & brokerage calculation

def calculate_transaction_costs(trade_value: float, is_sell: bool, config: dict) -> dict:
    """
    Calculates detailed round-trip transaction cost structure:
    Brokerage, Commodity Transaction Tax (CTT), GST, Stamp Duty, and Slippage.
    """
    costs_cfg = config.get("costs", {})
    
    # Base configuration values
    brokerage_per_order = costs_cfg.get("brokerage_per_order_inr", 20.0)
    gst_rate = costs_cfg.get("gst_rate", 0.18)
    ctt_rate = costs_cfg.get("ctt_rate", 0.0001)  # 0.01% on sell side
    stamp_duty_rate = costs_cfg.get("stamp_duty_rate", 0.00003)  # 0.003% on buy side
    slippage_ticks = costs_cfg.get("slippage_ticks", 1)
    tick_value_inr = 10.0  # Approx tick impact
    
    # Statutory & Brokerage Fees
    brokerage = brokerage_per_order
    gst = brokerage * gst_rate
    ctt = trade_value * ctt_rate if is_sell else 0.0
    stamp_duty = trade_value * stamp_duty_rate if not is_sell else 0.0
    slippage_cost = slippage_ticks * tick_value_inr
    
    total_cost_inr = brokerage + gst + ctt + stamp_duty + slippage_cost
    cost_in_bp = (total_cost_inr / trade_value) * 10000 if trade_value > 0 else 0.0
    
    return {
        "brokerage": round(brokerage, 2),
        "gst": round(gst, 2),
        "ctt": round(ctt, 2),
        "stamp_duty": round(stamp_duty, 2),
        "slippage": round(slippage_cost, 2),
        "total_cost_inr": round(total_cost_inr, 2),
        "cost_bp": round(cost_in_bp, 2)
    }

def estimate_roundtrip_cost_bp(
    brokerage_inr: float = 20.0, 
    slippage_ticks: int = 1, 
    notional_value: float = 75000.0,
    ctt_rate: float = 0.0001,
    stamp_duty_rate: float = 0.00003
) -> float:
    """
    Quick helper for UI slider calculations to estimate total roundtrip friction in basis points.
    """
    if notional_value <= 0:
        return 0.0
    
    # 2 orders (entry + exit) brokerage + GST (18%)
    total_brokerage = (brokerage_inr * 2) * 1.18
    # CTT on sell side + Stamp duty on buy side
    taxes = notional_value * (ctt_rate + stamp_duty_rate)
    # Slippage buffer on entry + exit
    slippage = slippage_ticks * 10.0 * 2
    
    total_friction = total_brokerage + taxes + slippage
    return round((total_friction / notional_value) * 10000, 2)