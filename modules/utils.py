def fmt_number(v: float) -> str:
    """Format float: strip trailing zeros, max 4 decimal places."""
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s or "0"
