import numpy as np

def calculate_component_var(exposures: np.ndarray, covariance_matrix: np.ndarray, total_var: float) -> np.ndarray:
    """
    Component VaR for Parametric VaR.
    Component VaR_i = (w_i * (Sigma * w)_i) / (w^T * Sigma * w) * Total VaR
    Since Total VaR = Z * sqrt(w^T * Sigma * w)
    Component VaR_i = (w_i * (Sigma * w)_i) / variance * Total VaR
    """
    if total_var == 0.0:
        return np.zeros_like(exposures)
        
    variance = exposures.T @ covariance_matrix @ exposures
    if variance <= 0.0:
        return np.zeros_like(exposures)
        
    _marginal_var = (covariance_matrix @ exposures) / np.sqrt(variance)
    
    # Component VaR = exposure * marginal_var * Z
    # We can also compute it as exposure * (Sigma * exposure) / variance * total_var
    component_var = (exposures * (covariance_matrix @ exposures)) / variance * total_var
    return component_var

def calculate_marginal_var(exposures: np.ndarray, covariance_matrix: np.ndarray, total_var: float) -> np.ndarray:
    """
    Marginal VaR is the partial derivative of Total VaR with respect to the exposure.
    Marginal VaR_i = d(VaR)/d(w_i) = Z * (Sigma * w)_i / sqrt(w^T * Sigma * w)
    = (Sigma * w)_i / variance * Total VaR
    """
    if total_var == 0.0:
        return np.zeros_like(exposures)
        
    variance = exposures.T @ covariance_matrix @ exposures
    if variance <= 0.0:
        return np.zeros_like(exposures)
        
    marginal_var = (covariance_matrix @ exposures) / variance * total_var
    return marginal_var
