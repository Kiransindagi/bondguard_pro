import logging

from app.db.database import SessionLocal
from app.db.models import CreditSpread, Instrument, MarketPrice, YieldCurvePoint
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_historical_coverage():
    db = SessionLocal()
    try:
        price_stats = db.query(
            Instrument.symbol, 
            func.count(MarketPrice.id), 
            func.min(MarketPrice.observation_date), 
            func.max(MarketPrice.observation_date)
        ).join(MarketPrice, Instrument.id == MarketPrice.instrument_id).group_by(Instrument.symbol).all()

        curve_stats = db.query(
            YieldCurvePoint.tenor_years, 
            func.count(YieldCurvePoint.id), 
            func.min(YieldCurvePoint.observation_date), 
            func.max(YieldCurvePoint.observation_date)
        ).group_by(YieldCurvePoint.tenor_years).all()

        credit_stats = db.query(
            CreditSpread.series_id, 
            func.count(CreditSpread.id), 
            func.min(CreditSpread.observation_date), 
            func.max(CreditSpread.observation_date)
        ).group_by(CreditSpread.series_id).all()

        logger.info("=== HISTORICAL DATA COVERAGE REPORT ===")
        logger.info("Market Prices (ETF):")
        for stat in price_stats:
            logger.info(f"  {stat[0]}: count={stat[1]}, min={stat[2]}, max={stat[3]}")

        logger.info("Yield Curve Points:")
        for stat in curve_stats:
            logger.info(f"  Tenor {stat[0]}Y: count={stat[1]}, min={stat[2]}, max={stat[3]}")

        logger.info("Credit Spreads:")
        for stat in credit_stats:
            logger.info(f"  Series {stat[0]}: count={stat[1]}, min={stat[2]}, max={stat[3]}")

    finally:
        db.close()

if __name__ == "__main__":
    check_historical_coverage()
