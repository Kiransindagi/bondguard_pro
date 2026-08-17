import numpy as np


def calculate_historical_var(pnl_vector: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Returns positive VaR currency loss magnitude.
    pnl_vector: array of scenario P&Ls (negative is loss).
    """
    if len(pnl_vector) == 0:
        return 0.0
    
    # Sort from worst loss (most negative) to best gain (most positive)
    sorted_pnl = np.sort(pnl_vector)
    
    # 95% confidence means the 5th percentile (0.05)
    quantile = 1.0 - confidence_level
    var_pnl = np.percentile(sorted_pnl, quantile * 100, method='higher')
    
    # VaR is reported as positive magnitude of loss
    var_currency = -var_pnl if var_pnl < 0 else 0.0
    return float(var_currency)

def calculate_expected_shortfall(pnl_vector: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Average loss beyond the VaR threshold.
    """
    if len(pnl_vector) == 0:
        return 0.0
        
    var_currency = calculate_historical_var(pnl_vector, confidence_level)
    
    # Losses beyond VaR threshold (losses worse than the VaR loss)
    # pnl_vector is negative for loss. var_currency is positive.
    # So threshold is -var_currency.
    threshold_pnl = -var_currency
    tail_losses = pnl_vector[pnl_vector <= threshold_pnl]
    
    if len(tail_losses) == 0:
        return float(var_currency)
        
    # Average of the tail losses (will be negative), return as positive magnitude
    es_currency = -float(np.mean(tail_losses))
    return es_currency
