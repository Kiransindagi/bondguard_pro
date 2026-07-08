from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Dict, Any, Optional
import pandas as pd

from app.db.models import MarketPrice, YieldCurvePoint, CreditSpread, Instrument
from app.risk_engine.exceptions import RiskEngineError

class HistoricalCoverageService:
    def __init__(self, db: Session):
        self.db = db

    def get_coverage_report(self) -> Dict[str, Any]:
        """
        Builds a historical coverage report across ETFs, Yield Curve, and Credit Spreads.
        """
        report = {
            "etf_prices": {},
            "yield_curve": {},
            "credit_spreads": {},
            "status": "ok"
        }
        
        # ETF Coverage
        etfs = self.db.query(
            Instrument.symbol, 
            func.count(MarketPrice.id), 
            func.min(MarketPrice.observation_date), 
            func.max(MarketPrice.observation_date)
        ).join(MarketPrice, Instrument.id == MarketPrice.instrument_id).group_by(Instrument.symbol).all()

        for etf in etfs:
            report["etf_prices"][etf.symbol] = self._format_stats(etf[1], etf[2], etf[3])
            
        # Yield Curve Coverage
        curves = self.db.query(
            YieldCurvePoint.tenor_years, 
            func.count(YieldCurvePoint.id), 
            func.min(YieldCurvePoint.observation_date), 
            func.max(YieldCurvePoint.observation_date)
        ).group_by(YieldCurvePoint.tenor_years).all()

        for curve in curves:
            report["yield_curve"][f"{curve[0]}Y"] = self._format_stats(curve[1], curve[2], curve[3])
            
        # Credit Spread Coverage
        spreads = self.db.query(
            CreditSpread.series_id, 
            func.count(CreditSpread.id), 
            func.min(CreditSpread.observation_date), 
            func.max(CreditSpread.observation_date)
        ).group_by(CreditSpread.series_id).all()

        for spread in spreads:
            report["credit_spreads"][spread[0]] = self._format_stats(spread[1], spread[2], spread[3])
            
        return report

    def _format_stats(self, count, min_date, max_date):
        freshness = "stale"
        if max_date:
            days_diff = (date.today() - max_date).days
            if days_diff <= 7:
                freshness = "fresh"
                
        # To determine missing values, we compare against expected business days,
        # but for a basic report we just show raw counts
        return {
            "count": count,
            "min_date": min_date.isoformat() if min_date else None,
            "max_date": max_date.isoformat() if max_date else None,
            "freshness": freshness
        }


class FactorAlignmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_aligned_factor_returns(self, start_date: Optional[date] = None, end_date: Optional[date] = None, required_obs: int = 252, model_status: str = "FULL_FACTOR_MODEL", include_etfs: bool = True) -> pd.DataFrame:
        """
        Builds a time-aligned DataFrame of daily factor shocks (basis point changes for rates/spreads, log returns for prices).
        No forward filling. Drops rows with missing data to ensure aligned shocks.
        """
        # Fetch Data
        etfs = pd.read_sql(self.db.query(MarketPrice.observation_date, Instrument.symbol, MarketPrice.close).join(Instrument).statement, self.db.connection())
        curves = pd.read_sql(self.db.query(YieldCurvePoint.observation_date, YieldCurvePoint.tenor_years, YieldCurvePoint.yield_percent).statement, self.db.connection())
        spreads = pd.read_sql(self.db.query(CreditSpread.observation_date, CreditSpread.series_id, CreditSpread.spread_bps).statement, self.db.connection())
        
        if etfs.empty and curves.empty and spreads.empty:
            raise RiskEngineError("Insufficient history: No data found.")

        if not etfs.empty:
            etf_pivot = etfs.pivot(index='observation_date', columns='symbol', values='close').sort_index()
        else:
            etf_pivot = pd.DataFrame()

        if not curves.empty:
            curves['tenor'] = curves['tenor_years'].apply(lambda x: f"RATE_{x}Y")
            curve_pivot = curves.pivot(index='observation_date', columns='tenor', values='yield_percent').sort_index()
        else:
            curve_pivot = pd.DataFrame()

        if not spreads.empty:
            spreads['series'] = spreads['series_id'].apply(lambda x: f"SPREAD_{x}")
            spread_pivot = spreads.pivot(index='observation_date', columns='series', values='spread_bps').sort_index()
        else:
            spread_pivot = pd.DataFrame()

        # Join raw data outer to align all dates
        dfs = [df for df in [etf_pivot, curve_pivot, spread_pivot] if not df.empty]
        if not dfs:
            raise RiskEngineError("Insufficient history: No computed returns/diffs.")

        # Outer join to gather all days correctly
        raw_aligned = dfs[0]
        for df in dfs[1:]:
            raw_aligned = raw_aligned.join(df, how='outer')

        # Compute differences. If a day is missing (NaN), diff will be NaN, so no multi-day shocks.
        aligned = pd.DataFrame(index=raw_aligned.index)
        
        for col in raw_aligned.columns:
            if col.startswith("RATE_"):
                aligned[col] = raw_aligned[col].diff() * 100.0
            elif col.startswith("SPREAD_"):
                aligned[col] = raw_aligned[col].diff()
            else:
                aligned[col] = raw_aligned[col].pct_change(fill_method=None)

        # Filter by date bounds before dropping NA (so we don't drop legitimate first-day NAs if they fall out of bounds anyway, though dropna drops them all)
        if start_date:
            aligned = aligned[aligned.index >= pd.to_datetime(start_date).date()]
        if end_date:
            aligned = aligned[aligned.index <= pd.to_datetime(end_date).date()]

        # Filter columns based on model status and ETF inclusion
        cols_to_keep = []
        for col in aligned.columns:
            if col.startswith("RATE_"):
                cols_to_keep.append(col)
            elif col.startswith("SPREAD_") and model_status == "FULL_FACTOR_MODEL":
                cols_to_keep.append(col)
            elif not col.startswith("RATE_") and not col.startswith("SPREAD_") and include_etfs:
                cols_to_keep.append(col)
                
        aligned = aligned[cols_to_keep]
        
        aligned = aligned.dropna(how='any')

        if len(aligned) < required_obs:
            raise RiskEngineError(f"Insufficient history: Found {len(aligned)} aligned observations, required {required_obs}.")

        return aligned

