from app.db.database import SessionLocal
from app.db.models import ConcentrationLimit


def seed_limits(db=None):
    is_local = False
    if db is None:
        db = SessionLocal()
        is_local = True
    try:
        limits = [
            {'limit_type': 'MAX_ISSUER_WEIGHT', 'threshold': 0.15, 'warning': 0.10},
            {'limit_type': 'MAX_SECTOR_WEIGHT', 'threshold': 0.40, 'warning': 0.30},
            {'limit_type': 'MAX_COUNTRY_WEIGHT', 'threshold': 0.60, 'warning': 0.50},
            {'limit_type': 'MAX_BELOW_INVESTMENT_GRADE_WEIGHT', 'threshold': 0.20, 'warning': 0.15},
            {'limit_type': 'MAX_OVER_20Y_MATURITY_WEIGHT', 'threshold': 0.25, 'warning': 0.20},
            {'limit_type': 'MAX_VERY_LOW_LIQUIDITY_WEIGHT', 'threshold': 0.10, 'warning': 0.05}
        ]
        
        for limit_dict in limits:
            existing = db.query(ConcentrationLimit).filter(
                ConcentrationLimit.limit_type == limit_dict['limit_type'],
                ConcentrationLimit.portfolio_id.is_(None)
            ).first()
            
            if not existing:
                lim = ConcentrationLimit(
                    portfolio_id=None,
                    limit_type=limit_dict['limit_type'],
                    threshold_value=limit_dict['threshold'],
                    warning_threshold_value=limit_dict['warning'],
                    is_active=True
                )
                db.add(lim)
        
        db.commit()
        print("Seeded demonstration concentration limits.")
    finally:
        if is_local:
            db.close()


if __name__ == "__main__":
    seed_limits()
