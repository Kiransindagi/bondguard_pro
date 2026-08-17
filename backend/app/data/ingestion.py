import logging
from datetime import date

from app.data.constants import ETF_SYMBOLS, TREASURY_SERIES
from app.data.fred_client import FredAPIClient
from app.data.market_client import YFinanceProvider
from app.data.repository import DataRepository
from app.data.transformations import (
    transform_fred_to_credit_spread,
    transform_fred_to_macro,
    transform_fred_to_yield_curve,
)
from app.data.validators import validate_market_price, validate_yield_curve_point
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DataIngestor:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DataRepository(db)
        self.fred_client = FredAPIClient()
        self.market_provider = YFinanceProvider()

    def ingest_fred_yield_curve(self, start_date: date | None = None, end_date: date | None = None):
        run = self.repo.start_ingestion_run("FRED", "Yield_Curve")
        try:
            total_fetched = 0
            total_inserted = 0
            for tenor, series_id in TREASURY_SERIES.items():
                logger.info(f"Fetching yield curve tenor {tenor} ({series_id})")
                raw_records = self.fred_client.fetch_series(series_id, start_date, end_date)
                transformed = transform_fred_to_yield_curve(raw_records)
                valid_records = [r for r in transformed if validate_yield_curve_point(r)]
                
                total_fetched += len(raw_records)
                inserted = self.repo.upsert_yield_curve_points(valid_records)
                total_inserted += inserted
                
            self.repo.finish_ingestion_run(run, "SUCCESS", total_fetched, total_inserted)
        except Exception as e:
            logger.error(f"Failed to ingest FRED Yield Curve: {e}")
            self.repo.finish_ingestion_run(run, "FAILED", error_message=str(e))

    def ingest_fred_credit_spreads(self, start_date: date | None = None, end_date: date | None = None):
        run = self.repo.start_ingestion_run("FRED", "Credit_Spreads")
        try:
            total_fetched = 0
            total_inserted = 0
            spread_series = ["BAMLC0A0CM", "BAMLH0A0HYM2"]
            for series_id in spread_series:
                logger.info(f"Fetching credit spread {series_id}")
                raw_records = self.fred_client.fetch_series(series_id, start_date, end_date)
                transformed = transform_fred_to_credit_spread(raw_records)
                
                total_fetched += len(raw_records)
                inserted = self.repo.upsert_credit_spreads(transformed)
                total_inserted += inserted
                
            self.repo.finish_ingestion_run(run, "SUCCESS", total_fetched, total_inserted)
        except Exception as e:
            logger.error(f"Failed to ingest FRED Credit Spreads: {e}")
            self.repo.finish_ingestion_run(run, "FAILED", error_message=str(e))

    def ingest_fred_macro(self, start_date: date | None = None, end_date: date | None = None):
        run = self.repo.start_ingestion_run("FRED", "Macro")
        try:
            total_fetched = 0
            total_inserted = 0
            macro_series = ["DFF"]
            for series_id in macro_series:
                logger.info(f"Fetching macro series {series_id}")
                raw_records = self.fred_client.fetch_series(series_id, start_date, end_date)
                transformed = transform_fred_to_macro(raw_records)
                
                total_fetched += len(raw_records)
                inserted = self.repo.upsert_macro_observations(transformed)
                total_inserted += inserted
                
            self.repo.finish_ingestion_run(run, "SUCCESS", total_fetched, total_inserted)
        except Exception as e:
            logger.error(f"Failed to ingest FRED Macro: {e}")
            self.repo.finish_ingestion_run(run, "FAILED", error_message=str(e))

    def ingest_etf_market_data(self, start_date: date | None = None, end_date: date | None = None):
        run = self.repo.start_ingestion_run("yfinance", "ETF_Market_Data")
        try:
            total_fetched = 0
            total_inserted = 0
            for symbol in ETF_SYMBOLS:
                logger.info(f"Fetching market data for {symbol}")
                inst = self.repo.get_or_create_instrument(symbol, symbol)
                raw_records = self.market_provider.fetch_historical_prices(symbol, start_date, end_date)
                
                valid_records = [r for r in raw_records if validate_market_price(r)]
                
                total_fetched += len(raw_records)
                inserted = self.repo.upsert_market_prices(inst.id, valid_records)
                total_inserted += inserted
                
            self.repo.finish_ingestion_run(run, "SUCCESS", total_fetched, total_inserted)
        except Exception as e:
            logger.error(f"Failed to ingest ETF Market Data: {e}")
            self.repo.finish_ingestion_run(run, "FAILED", error_message=str(e))

    def ingest_all(self, start_date: date | None = None, end_date: date | None = None):
        self.ingest_fred_yield_curve(start_date, end_date)
        self.ingest_fred_credit_spreads(start_date, end_date)
        self.ingest_fred_macro(start_date, end_date)
        self.ingest_etf_market_data(start_date, end_date)
