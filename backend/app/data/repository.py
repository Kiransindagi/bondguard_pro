from datetime import datetime, timezone
from typing import Any

from app.db.models import (
    CreditSpread,
    DataIngestionRun,
    Instrument,
    MacroObservation,
    MarketPrice,
    YieldCurvePoint,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


class DataRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_market_prices(self, instrument_id: int, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
            
        for r in records:
            r["instrument_id"] = instrument_id
            
        stmt = insert(MarketPrice).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_market_price_obs',
            set_={
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'adjusted_close': stmt.excluded.adjusted_close,
                'volume': stmt.excluded.volume,
                'ingested_at': stmt.excluded.ingested_at
            }
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def upsert_yield_curve_points(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
            
        stmt = insert(YieldCurvePoint).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_yield_curve_obs',
            set_={
                'yield_percent': stmt.excluded.yield_percent,
                'series_id': stmt.excluded.series_id,
                'ingested_at': stmt.excluded.ingested_at
            }
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def upsert_credit_spreads(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
            
        stmt = insert(CreditSpread).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_credit_spread_obs',
            set_={
                'spread_bps': stmt.excluded.spread_bps,
                'series_id': stmt.excluded.series_id,
                'ingested_at': stmt.excluded.ingested_at
            }
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def upsert_macro_observations(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
            
        stmt = insert(MacroObservation).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_macro_obs',
            set_={
                'value': stmt.excluded.value,
                'source': stmt.excluded.source,
                'ingested_at': stmt.excluded.ingested_at
            }
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def get_or_create_instrument(self, symbol: str, name: str, instrument_type: str = "ETF", asset_class: str = "Fixed Income") -> Instrument:
        inst = self.db.query(Instrument).filter(Instrument.symbol == symbol).first()
        if not inst:
            inst = Instrument(
                symbol=symbol,
                name=name,
                instrument_type=instrument_type,
                asset_class=asset_class,
                currency="USD"
            )
            self.db.add(inst)
            self.db.commit()
            self.db.refresh(inst)
        return inst

    def start_ingestion_run(self, source: str, dataset: str) -> DataIngestionRun:
        run = DataIngestionRun(
            source=source,
            dataset=dataset,
            status="RUNNING"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def finish_ingestion_run(self, run: DataIngestionRun, status: str, fetched: int = 0, inserted: int = 0, error_message: str | None = None):
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        run.records_fetched = fetched
        run.records_inserted = inserted
        run.error_message = error_message
        self.db.commit()
        self.db.refresh(run)
