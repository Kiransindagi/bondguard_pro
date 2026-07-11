from decimal import Decimal
from datetime import date
from typing import Dict
from sqlalchemy.orm import Session

from app.db.models import Bond
from app.risk_engine.types import BondRiskInput
from app.risk_engine.position_risk import calculate_position_risk
from app.risk_engine.curve import YieldCurve

TENOR_NODES = {
    "2Y": 2.0,
    "5Y": 5.0,
    "10Y": 10.0,
    "30Y": 30.0
}

def calculate_tenor_weights(maturity_years: float) -> Dict[str, float]:
    """
    Linearly interpolate weights for the key tenors 2Y, 5Y, 10Y, 30Y.
    The sum of weights equals 1.0.
    """
    t1, t2, t3, t4 = 2.0, 5.0, 10.0, 30.0
    weights = {"2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0}

    if maturity_years <= t1:
        weights["2Y"] = 1.0
    elif t1 < maturity_years <= t2:
        weights["2Y"] = (t2 - maturity_years) / (t2 - t1)
        weights["5Y"] = (maturity_years - t1) / (t2 - t1)
    elif t2 < maturity_years <= t3:
        weights["5Y"] = (t3 - maturity_years) / (t3 - t2)
        weights["10Y"] = (maturity_years - t2) / (t3 - t2)
    elif t3 < maturity_years <= t4:
        weights["10Y"] = (t4 - maturity_years) / (t4 - t3)
        weights["30Y"] = (maturity_years - t3) / (t4 - t3)
    else:
        weights["30Y"] = 1.0

    return weights

class AdvancedAnalyticsCalculator:
    @staticmethod
    def calculate_key_rate_duration(
        bond: Bond,
        valuation_date: date,
        clean_price: Decimal,
        quantity: Decimal
    ) -> Dict[str, float]:
        """
        Calculate Key Rate Duration (KRD) for tenors 2Y, 5Y, 10Y, 30Y.
        """
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=clean_price,
            quantity=quantity
        )
        base_risk = calculate_position_risk(input_data)
        mod_dur = float(base_risk.modified_duration_years)
        
        maturity_years = max(0.0, (bond.maturity_date - valuation_date).days / 365.25)
        weights = calculate_tenor_weights(maturity_years)
        
        # Approximate Key Rate Durations: KRD_i = weight_i * ModifiedDuration
        return {
            "KRD_2Y": round(weights["2Y"] * mod_dur, 6),
            "KRD_5Y": round(weights["5Y"] * mod_dur, 6),
            "KRD_10Y": round(weights["10Y"] * mod_dur, 6),
            "KRD_30Y": round(weights["30Y"] * mod_dur, 6)
        }

    @staticmethod
    def calculate_bucketed_dv01(
        bond: Bond,
        valuation_date: date,
        clean_price: Decimal,
        quantity: Decimal
    ) -> Dict[str, float]:
        """
        Calculate tenor-bucketed DV01 values.
        """
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=clean_price,
            quantity=quantity
        )
        base_risk = calculate_position_risk(input_data)
        base_dv01 = float(base_risk.dv01_currency)
        
        maturity_years = max(0.0, (bond.maturity_date - valuation_date).days / 365.25)
        weights = calculate_tenor_weights(maturity_years)
        
        return {
            "DV01_2Y": round(weights["2Y"] * base_dv01, 6),
            "DV01_5Y": round(weights["5Y"] * base_dv01, 6),
            "DV01_10Y": round(weights["10Y"] * base_dv01, 6),
            "DV01_30Y": round(weights["30Y"] * base_dv01, 6)
        }

    @staticmethod
    def calculate_spread_risk(
        bond: Bond,
        valuation_date: date,
        clean_price: Decimal,
        quantity: Decimal
    ) -> Dict[str, float]:
        """
        Calculate Spread Duration and CS01.
        Treasuries have zero spread risk.
        """
        is_corporate = getattr(bond, "bond_type", None) == "Corporate"
        
        if not is_corporate:
            return {
                "spread_duration": 0.0,
                "cs01": 0.0
            }
            
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=clean_price,
            quantity=quantity
        )
        base_risk = calculate_position_risk(input_data)
        
        return {
            "spread_duration": round(float(base_risk.modified_duration_years), 6),
            "cs01": round(float(base_risk.dv01_currency), 6)
        }

def get_yield_curve(db: Session, valuation_date: date) -> YieldCurve:
    from app.db.models import YieldCurvePoint
    from app.risk_engine.curve import YieldCurve
    from sqlalchemy import func
    latest_date = db.query(func.max(YieldCurvePoint.observation_date)).scalar()
    if not latest_date:
        return YieldCurve({2.0: Decimal('0.04'), 5.0: Decimal('0.04'), 10.0: Decimal('0.04'), 30.0: Decimal('0.04')})
    pts = db.query(YieldCurvePoint).filter(YieldCurvePoint.observation_date == latest_date).all()
    points_dict = {float(p.tenor): Decimal(str(p.rate)) / Decimal('100.0') for p in pts}
    if not points_dict:
        return YieldCurve({2.0: Decimal('0.04'), 5.0: Decimal('0.04'), 10.0: Decimal('0.04'), 30.0: Decimal('0.04')})
    return YieldCurve(points_dict)

class CarryRollDownCalculator:
    @staticmethod
    def calculate_carry_roll_down(
        db: Session,
        bond: Bond,
        valuation_date: date,
        clean_price: Decimal,
        quantity: Decimal,
        horizon_months: int = 1
    ) -> Dict[str, float]:
        """
        Calculate coupon carry, yield carry, roll-down and projected return for a horizon in months.
        """
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=clean_price,
            quantity=quantity
        )
        base_risk = calculate_position_risk(input_data)
        ytm = float(base_risk.ytm_decimal)
        mod_dur = float(base_risk.modified_duration_years)
        
        horizon_years = horizon_months / 12.0
        
        # Coupon carry
        coupon_carry = float(bond.coupon_rate) * horizon_years
        
        # Yield carry
        yield_carry = ytm * horizon_years
        
        # Roll-down
        curve = get_yield_curve(db, valuation_date)
        maturity_years = max(0.0, (bond.maturity_date - valuation_date).days / 365.25)
        
        y_curr = float(curve.get_yield(maturity_years))
        future_tenor = max(0.0, maturity_years - horizon_years)
        y_future = float(curve.get_yield(future_tenor))
        
        roll_down_yield_shift = y_future - y_curr
        roll_down_return = -mod_dur * roll_down_yield_shift
        
        projected_return = yield_carry + roll_down_return
        
        return {
            "coupon_carry": round(coupon_carry * 100.0, 6),
            "yield_carry": round(yield_carry * 100.0, 6),
            "roll_down_return": round(roll_down_return * 100.0, 6),
            "projected_return": round(projected_return * 100.0, 6)
        }

class PnLExplainCalculator:
    @staticmethod
    def calculate_pnl_explain(
        bond: Bond,
        valuation_date: date,
        clean_price: Decimal,
        quantity: Decimal,
        rate_shock_bps: float,
        spread_shock_bps: float,
        actual_pnl: float
    ) -> Dict[str, float]:
        """
        Decompose bond return into explained components (carry, rate, spread, convexity) and residual.
        """
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=clean_price,
            quantity=quantity
        )
        base_risk = calculate_position_risk(input_data)
        
        horizon_days = 1.0
        carry = float(base_risk.ytm_decimal) * (horizon_days / 365.25) * float(base_risk.market_value)
        
        dv01 = float(base_risk.dv01_currency)
        rate_pnl = -dv01 * rate_shock_bps
        
        is_corporate = getattr(bond, "bond_type", None) == "Corporate"
        cs01 = dv01 if is_corporate else 0.0
        spread_pnl = -cs01 * spread_shock_bps
        
        total_shock_dec = (rate_shock_bps + (spread_shock_bps if is_corporate else 0.0)) / 10000.0
        conv = float(base_risk.convexity)
        mv = float(base_risk.market_value)
        convexity_pnl = 0.5 * conv * mv * (total_shock_dec ** 2)
        
        explained_pnl = carry + rate_pnl + spread_pnl + convexity_pnl
        residual = actual_pnl - explained_pnl
        
        return {
            "carry": round(carry, 6),
            "rate_pnl": round(rate_pnl, 6),
            "spread_pnl": round(spread_pnl, 6),
            "convexity_pnl": round(convexity_pnl, 6),
            "explained_pnl": round(explained_pnl, 6),
            "residual": round(residual, 6),
            "actual_pnl": round(actual_pnl, 6)
        }
