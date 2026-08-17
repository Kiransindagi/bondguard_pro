from typing import Any

import numpy as np
from app.risk_engine.market_risk.historical_var import calculate_historical_var


def calculate_backtest(pnl_vector: np.ndarray, confidence_level: float = 0.95, window: int = 252) -> dict[str, Any]:
    """
    VaR backtesting using rolling estimation windows.
    pnl_vector: actual daily P&Ls.
    """
    if len(pnl_vector) <= window:
        return {
            "status": "Insufficient history for backtesting",
            "exceptions": 0,
            "exception_rate": 0.0,
            "expected_rate": 1.0 - confidence_level,
            "total_tested": 0
        }
        
    exceptions = 0
    total_tested = len(pnl_vector) - window
    results = []
    
    for i in range(window, len(pnl_vector)):
        # Historical window strictly BEFORE the realized P&L
        hist_window = pnl_vector[i - window : i]
        realized_pnl = pnl_vector[i]
        
        # Calculate VaR on historical window
        # calculate_historical_var returns positive VaR magnitude
        var_currency = calculate_historical_var(hist_window, confidence_level)
        
        # Exception if realized P&L is worse (more negative) than -VaR
        is_exception = realized_pnl < -var_currency
        if is_exception:
            exceptions += 1
            
        results.append({
            "day": i,
            "realized_pnl": float(realized_pnl),
            "var_estimate": float(var_currency),
            "is_exception": bool(is_exception)
        })
        
    exception_rate = exceptions / total_tested
    expected_rate = 1.0 - confidence_level
    
    return {
        "status": "SUCCESS",
        "exceptions": exceptions,
        "exception_rate": float(exception_rate),
        "expected_rate": float(expected_rate),
        "total_tested": total_tested,
        "details": results
    }
