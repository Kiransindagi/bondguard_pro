import argparse
import logging
from datetime import datetime

from app.data.ingestion import DataIngestor
from app.db.database import SessionLocal

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="BondGuard Pro Data Ingestion CLI")
    parser.add_argument("--dataset", type=str, choices=["yield_curve", "credit_spreads", "macro", "etf", "all"], required=True, help="Dataset to ingest")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else None
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else None
    
    db = SessionLocal()
    ingestor = DataIngestor(db)
    
    try:
        if args.dataset == "yield_curve":
            ingestor.ingest_fred_yield_curve(start_date, end_date)
        elif args.dataset == "credit_spreads":
            ingestor.ingest_fred_credit_spreads(start_date, end_date)
        elif args.dataset == "macro":
            ingestor.ingest_fred_macro(start_date, end_date)
        elif args.dataset == "etf":
            ingestor.ingest_etf_market_data(start_date, end_date)
        elif args.dataset == "all":
            ingestor.ingest_all(start_date, end_date)
    finally:
        db.close()

if __name__ == "__main__":
    main()
