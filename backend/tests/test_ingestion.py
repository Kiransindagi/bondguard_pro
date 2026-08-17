from datetime import date
from unittest.mock import patch

from app.data.ingestion import DataIngestor
from app.db.models import DataIngestionRun, MarketPrice, YieldCurvePoint


def test_fred_yield_curve_ingestion_mock(client, db_session):
    ingestor = DataIngestor(db_session)
    
    with patch('app.data.fred_client.FredAPIClient.fetch_series') as mock_fetch:
        def fetch_side_effect(series_id, *args, **kwargs):
            return [{"observation_date": date(2023, 1, 1), "value": 4.25, "series_id": series_id, "source": "FRED"}]
        mock_fetch.side_effect = fetch_side_effect
        
        ingestor.ingest_fred_yield_curve()
        
        # Verify persistence
        points = db_session.query(YieldCurvePoint).all()
        assert len(points) == 4 # One for each tenor because of the mock
        assert points[0].yield_percent == 4.25
        
        # Verify idempotency
        ingestor.ingest_fred_yield_curve()
        points = db_session.query(YieldCurvePoint).all()
        assert len(points) == 4
        
        # Verify run state
        runs = db_session.query(DataIngestionRun).filter(DataIngestionRun.dataset == "Yield_Curve").all()
        assert len(runs) == 2
        assert runs[0].status == "SUCCESS"

def test_etf_market_data_ingestion_mock(client, db_session):
    ingestor = DataIngestor(db_session)
    
    with patch('app.data.market_client.YFinanceProvider.fetch_historical_prices') as mock_fetch:
        mock_fetch.return_value = [
            {
                "observation_date": date(2023, 1, 1),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
                "adjusted_close": 100.5,
                "source": "yfinance"
            }
        ]
        
        ingestor.ingest_etf_market_data()
        
        prices = db_session.query(MarketPrice).all()
        assert len(prices) == 6 # 6 ETFs
        assert prices[0].close == 100.5
