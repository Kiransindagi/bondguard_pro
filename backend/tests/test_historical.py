import pytest
from datetime import date
from app.db.models import Instrument, MarketPrice, YieldCurvePoint, CreditSpread
from app.risk_engine.historical import HistoricalCoverageService, FactorAlignmentService
from app.risk_engine.exceptions import RiskEngineError

def test_coverage_service(db_session):
    # Insert some mock data
    inst = Instrument(symbol="MOCK_ETF", name="Mock ETF", instrument_type="ETF", asset_class="Equity", currency="USD")
    db_session.add(inst)
    db_session.commit()
    
    mp = MarketPrice(instrument_id=inst.id, observation_date=date(2023, 1, 1), open=100.0, high=100.0, low=100.0, close=100.0, volume=100, source="yfinance")
    db_session.add(mp)
    
    yp = YieldCurvePoint(observation_date=date(2023, 1, 1), tenor_years=2.0, yield_percent=4.0, series_id="DGS2", source="FRED")
    db_session.add(yp)
    
    cp = CreditSpread(observation_date=date(2023, 1, 1), series_id="BAMLC0A0CM", spread_type="OAS", spread_bps=150.0, source="FRED")
    db_session.add(cp)
    
    db_session.commit()

    service = HistoricalCoverageService(db_session)
    report = service.get_coverage_report()
    
    assert "MOCK_ETF" in report["etf_prices"]
    assert report["etf_prices"]["MOCK_ETF"]["count"] >= 1
    
    assert "2.0Y" in report["yield_curve"]
    assert report["yield_curve"]["2.0Y"]["count"] >= 1
    
    assert "BAMLC0A0CM" in report["credit_spreads"]
    assert report["credit_spreads"]["BAMLC0A0CM"]["count"] >= 1

def test_alignment_service_insufficient_data(db_session):
    service = FactorAlignmentService(db_session)
    # Even with mock data, it has only 1 point, diff/pct_change needs 2, and we require 252.
    with pytest.raises(RiskEngineError) as exc:
        service.get_aligned_factor_returns(required_obs=252)
    assert "Insufficient history" in str(exc.value)

def test_alignment_logic_mocked_db(db_session):
    # Remove all data from test db to cleanly test alignment
    db_session.query(MarketPrice).delete()
    db_session.query(YieldCurvePoint).delete()
    db_session.query(CreditSpread).delete()
    db_session.query(Instrument).delete()
    db_session.commit()

    inst = Instrument(symbol="TEST_ETF", name="Test", instrument_type="ETF", asset_class="Equity", currency="USD")
    db_session.add(inst)
    db_session.commit()

    # Add 4 days of data to test returns calculation
    dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3), date(2023, 1, 4)]
    prices = [100.0, 101.0, 102.0, 100.0]
    yields = [4.0, 4.1, 4.0, 4.2] # 4.1 - 4.0 = 0.1 -> 10 bps
    spreads = [1.5, 1.6, 1.5, 1.4] # 1.6 - 1.5 = 0.1 -> 10 bps

    for d, p, y, s in zip(dates, prices, yields, spreads):
        db_session.add(MarketPrice(instrument_id=inst.id, observation_date=d, open=p, high=p, low=p, close=p, volume=100, source="yfinance"))
        db_session.add(YieldCurvePoint(observation_date=d, tenor_years=2.0, yield_percent=y, series_id="DGS2", source="FRED"))
        db_session.add(CreditSpread(observation_date=d, series_id="BAMLC0A0CM", spread_type="OAS", spread_bps=s * 100, source="FRED"))
    
    db_session.commit()

    service = FactorAlignmentService(db_session)
    df = service.get_aligned_factor_returns(required_obs=3)
    
    # 4 days -> 3 days of returns/diffs
    assert len(df) == 3
    
    # Check return for date 2023-01-02
    assert "TEST_ETF" in df.columns
    assert "RATE_2.0Y" in df.columns
    assert "SPREAD_BAMLC0A0CM" in df.columns

    row2 = df.iloc[0]
    assert round(row2["TEST_ETF"], 4) == round(0.01, 4) # (101 - 100) / 100
    assert round(row2["RATE_2.0Y"], 2) == 10.0 # (4.1 - 4.0) * 100 bps
    assert round(row2["SPREAD_BAMLC0A0CM"], 2) == 10.0

def test_missing_dates_alignment(db_session):
    db_session.query(MarketPrice).delete()
    db_session.query(YieldCurvePoint).delete()
    db_session.query(CreditSpread).delete()
    db_session.query(Instrument).delete()
    
    inst = Instrument(symbol="T2", name="T2", instrument_type="ETF", asset_class="Equity", currency="USD")
    db_session.add(inst)
    db_session.commit()
    
    # Day 1 - all exist
    d1 = date(2023, 1, 1)
    db_session.add(MarketPrice(instrument_id=inst.id, observation_date=d1, open=100.0, high=100.0, low=100.0, close=100.0, volume=100, source="yfinance"))
    db_session.add(YieldCurvePoint(observation_date=d1, tenor_years=2.0, yield_percent=4.0, series_id="DGS2", source="FRED"))
    
    # Day 2 - price exists, curve missing
    d2 = date(2023, 1, 2)
    db_session.add(MarketPrice(instrument_id=inst.id, observation_date=d2, open=101.0, high=101.0, low=101.0, close=101.0, volume=100, source="yfinance"))
    
    # Day 3 - all exist
    d3 = date(2023, 1, 3)
    db_session.add(MarketPrice(instrument_id=inst.id, observation_date=d3, open=102.0, high=102.0, low=102.0, close=102.0, volume=100, source="yfinance"))
    db_session.add(YieldCurvePoint(observation_date=d3, tenor_years=2.0, yield_percent=4.1, series_id="DGS2", source="FRED"))
    db_session.commit()

    service = FactorAlignmentService(db_session)
    with pytest.raises(RiskEngineError):
        # We only have one valid diff row? Wait, day 2 curve is missing. 
        # day 2 pct_change is NaN for curve.
        # day 3 pct_change is 4.1 - NaN = NaN
        # The inner join and dropna() should result in 0 aligned rows.
        # required_obs=1 should fail.
        service.get_aligned_factor_returns(required_obs=1)

