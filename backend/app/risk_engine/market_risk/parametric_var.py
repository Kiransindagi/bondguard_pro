import numpy as np
from scipy.stats import norm


def calculate_parametric_var(exposures: np.ndarray, covariance_matrix: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Parametric VaR = Z * sqrt(w^T * Sigma * w)
    where Z is the normal quantile for the given confidence level.
    exposures: currency sensitivities (e.g. -DV01) vector aligned with covariance matrix.
    covariance_matrix: covariance of factor shocks.
    """
    variance = exposures.T @ covariance_matrix @ exposures
    
    if variance <= 0.0:
        return 0.0
        
    std_dev = np.sqrt(variance)
    
    # 95% confidence means 1-tail Z-score
    z_score = norm.ppf(confidence_level)
    
    var_currency = z_score * std_dev
    return float(var_currency)
