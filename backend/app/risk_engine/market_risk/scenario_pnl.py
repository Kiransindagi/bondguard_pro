from typing import Any

import pandas as pd
from app.risk_engine.market_risk.factor_mapping import FactorMappingService
from app.risk_engine.types import BondRiskResult


class ScenarioPnlMatrix:
    def __init__(self, aligned_shocks: pd.DataFrame):
        self.shocks = aligned_shocks

    def compute_matrix(self, positions_risk: list[BondRiskResult], bonds_map: dict[int, Any]) -> pd.DataFrame:
        """
        Rows: dates
        Cols: bond_ids
        Values: P&L
        """
        pnl_matrix = pd.DataFrame(index=self.shocks.index)
        
        for pos in positions_risk:
            bond = bonds_map[pos.bond_id]
            # Get exposures
            dv01 = float(pos.dv01_currency)
            # Approximate CS01 = DV01 for now as per instructions (approximate spread sensitivity)
            cs01 = dv01 if getattr(bond, "bond_type", None) == "Corporate" else 0.0
            
            rate_factor = FactorMappingService.get_rate_factor_for_tenor(pos.modified_duration_years)
            spread_factor = FactorMappingService.get_spread_factor_for_bond(bond)
            
            # P&L = -DV01 * rate_shock - CS01 * spread_shock
            pnl = pd.Series(0.0, index=self.shocks.index)
            
            if rate_factor in self.shocks.columns:
                pnl += -dv01 * self.shocks[rate_factor]
                
            if spread_factor and spread_factor in self.shocks.columns:
                pnl += -cs01 * self.shocks[spread_factor]
                
            pnl_matrix[pos.bond_id] = pnl
            
        pnl_matrix["PORTFOLIO"] = pnl_matrix.sum(axis=1)
        return pnl_matrix
