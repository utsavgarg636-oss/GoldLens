# Step 4: Signal generation

def generate_pair_signals(z_score: float, entry_threshold: float = 2.0) -> str:
    """
    Generates Long/Short signals based on z-score deviation.
    """
    if z_score >= entry_threshold:
        return "SHORT_RICH_LONG_CHEAP"
    elif z_score <= -entry_threshold:
        return "LONG_CHEAP_SHORT_RICH"
    return "NO_SIGNAL"