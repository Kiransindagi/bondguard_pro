from app.db.database import SessionLocal
from app.db.models import LiquidityAssumption
from app.risk_engine.liquidity_risk import DEFAULT_ASSUMPTIONS

def seed_assumptions(db=None):
    is_local = False
    if db is None:
        db = SessionLocal()
        is_local = True
    try:
        existing = db.query(LiquidityAssumption).filter(LiquidityAssumption.name == 'BondGuard Default V1').first()
        if existing:
            print("Default liquidity assumption already exists.")
            return

        assumption = LiquidityAssumption(
            name='BondGuard Default V1',
            version=DEFAULT_ASSUMPTIONS.version,
            description="Default characteristic-based proxy liquidity assumption",
            methodology="CHARACTERISTIC_BASED_PROXY_V1",
            configuration_json=DEFAULT_ASSUMPTIONS.dict(),
            is_active=True
        )
        db.add(assumption)
        db.commit()
        print("Seeded default liquidity assumption.")
    finally:
        if is_local:
            db.close()


if __name__ == "__main__":
    seed_assumptions()
