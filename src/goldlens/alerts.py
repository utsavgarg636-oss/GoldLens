# Step 5: Quiet alerts logic

def evaluate_quiet_alert_gate(z_score: float, exp_edge_bp: float, est_cost_bp: float) -> dict:
    """
    Quiet Alert Gate: Only fires if edge > cost.
    """
    if abs(z_score) < 2.0:
        return {"passed": False, "reason": "Z-score below entry threshold (2.0)"}
    if exp_edge_bp <= est_cost_bp:
        return {"passed": False, "reason": f"Expected edge ({exp_edge_bp:.1f} bp) < Cost ({est_cost_bp:.1f} bp)"}
    
    return {"passed": True, "reason": "Actionable relative value signal detected!"}