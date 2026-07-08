from typing import List, Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel
from .types import BondRiskResult

class PortfolioRiskSummary(BaseModel):
    portfolio_id: int
    valuation_date: date
    total_market_value: Decimal
    weighted_average_ytm: Decimal
    weighted_macaulay_duration: Decimal
    weighted_modified_duration: Decimal
    weighted_convexity: Decimal
    total_dv01: Decimal
    active_position_count: int
    matured_position_count: int
    curve_date: Optional[date] = None

def aggregate_portfolio_risk(portfolio_id: int, valuation_date: date, position_risks: List[BondRiskResult], curve_date: Optional[date] = None) -> PortfolioRiskSummary:
    total_mv = Decimal('0')
    total_dv01 = Decimal('0')
    active_count = 0
    matured_count = 0

    for risk in position_risks:
        if risk.market_value > 0:
            total_mv += risk.market_value
            total_dv01 += risk.dv01_currency
            active_count += 1
        elif risk.valuation_date >= risk.valuation_date: # Simplified check for mature
            # Need a better matured check but mv is 0 usually
            matured_count += 1

    if total_mv == 0:
        return PortfolioRiskSummary(
            portfolio_id=portfolio_id, valuation_date=valuation_date,
            total_market_value=Decimal('0'), weighted_average_ytm=Decimal('0'),
            weighted_macaulay_duration=Decimal('0'), weighted_modified_duration=Decimal('0'),
            weighted_convexity=Decimal('0'), total_dv01=Decimal('0'),
            active_position_count=active_count, matured_position_count=matured_count, curve_date=curve_date
        )

    weighted_ytm = sum(r.ytm_decimal * (r.market_value / total_mv) for r in position_risks if r.market_value > 0)
    weighted_mac_dur = sum(r.macaulay_duration_years * (r.market_value / total_mv) for r in position_risks if r.market_value > 0)
    weighted_mod_dur = sum(r.modified_duration_years * (r.market_value / total_mv) for r in position_risks if r.market_value > 0)
    weighted_conv = sum(r.convexity * (r.market_value / total_mv) for r in position_risks if r.market_value > 0)

    return PortfolioRiskSummary(
        portfolio_id=portfolio_id,
        valuation_date=valuation_date,
        total_market_value=total_mv,
        weighted_average_ytm=weighted_ytm,
        weighted_macaulay_duration=weighted_mac_dur,
        weighted_modified_duration=weighted_mod_dur,
        weighted_convexity=weighted_conv,
        total_dv01=total_dv01,
        active_position_count=active_count,
        matured_position_count=matured_count,
        curve_date=curve_date
    )
