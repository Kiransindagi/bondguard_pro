import pandas as pd
from typing import Dict, Any

def calculate_covariance_matrix(shocks: pd.DataFrame) -> Dict[str, Any]:
    cov = shocks.cov()
    
    return {
        "factors": list(cov.columns),
        "matrix": cov.values.tolist(),
        "observation_count": len(shocks),
        "start_date": shocks.index.min().isoformat() if not shocks.empty else None,
        "end_date": shocks.index.max().isoformat() if not shocks.empty else None
    }

def calculate_correlation_matrix(shocks: pd.DataFrame) -> Dict[str, Any]:
    corr = shocks.corr()
    
    return {
        "factors": list(corr.columns),
        "matrix": corr.values.tolist(),
        "observation_count": len(shocks),
        "start_date": shocks.index.min().isoformat() if not shocks.empty else None,
        "end_date": shocks.index.max().isoformat() if not shocks.empty else None
    }
