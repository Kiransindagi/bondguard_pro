import pandas as pd
from typing import Dict, Any

def calculate_rolling_volatility(shocks: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
    # We compute rolling standard deviation (volatility) of shocks
    # Since rate/spread shocks are daily bps, vol is daily bps vol
    vol = shocks.rolling(window=window).std()
    # Drop rows where vol is NaN due to rolling window
    vol = vol.dropna(how='all')
    
    vol_reset = vol.reset_index()
    vol_reset['observation_date'] = vol_reset['observation_date'].astype(str)
    
    return {
        "window": window,
        "data": vol_reset.to_dict(orient="records")
    }
