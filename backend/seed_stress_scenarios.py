import os
import sys
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, StressScenario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCENARIOS = [
    # Parallel Rate Shocks
    {"name": "RATE_UP_25BP", "scenario_type": "PARALLEL_RATE", "r": 25.0},
    {"name": "RATE_UP_50BP", "scenario_type": "PARALLEL_RATE", "r": 50.0},
    {"name": "RATE_UP_100BP", "scenario_type": "PARALLEL_RATE", "r": 100.0},
    {"name": "RATE_UP_200BP", "scenario_type": "PARALLEL_RATE", "r": 200.0},
    {"name": "RATE_DOWN_25BP", "scenario_type": "PARALLEL_RATE", "r": -25.0},
    {"name": "RATE_DOWN_50BP", "scenario_type": "PARALLEL_RATE", "r": -50.0},
    {"name": "RATE_DOWN_100BP", "scenario_type": "PARALLEL_RATE", "r": -100.0},
    {"name": "RATE_DOWN_200BP", "scenario_type": "PARALLEL_RATE", "r": -200.0},
    
    # Steepener/Flattener
    {
        "name": "BEAR_STEEPENER",
        "scenario_type": "NON_PARALLEL_RATE",
        "rate_2y_shock_bps": 50.0,
        "rate_5y_shock_bps": 75.0,
        "rate_10y_shock_bps": 100.0,
        "rate_30y_shock_bps": 125.0
    },
    {
        "name": "BULL_STEEPENER",
        "scenario_type": "NON_PARALLEL_RATE",
        "rate_2y_shock_bps": -100.0,
        "rate_5y_shock_bps": -75.0,
        "rate_10y_shock_bps": -50.0,
        "rate_30y_shock_bps": -25.0
    },
    {
        "name": "BEAR_FLATTENER",
        "scenario_type": "NON_PARALLEL_RATE",
        "rate_2y_shock_bps": 125.0,
        "rate_5y_shock_bps": 100.0,
        "rate_10y_shock_bps": 75.0,
        "rate_30y_shock_bps": 50.0
    },
    {
        "name": "BULL_FLATTENER",
        "scenario_type": "NON_PARALLEL_RATE",
        "rate_2y_shock_bps": -25.0,
        "rate_5y_shock_bps": -50.0,
        "rate_10y_shock_bps": -75.0,
        "rate_30y_shock_bps": -100.0
    },
    
    # Credit Spreads
    {"name": "IG_SPREAD_WIDEN_25BP", "scenario_type": "CREDIT_SPREAD", "ig": 25.0},
    {"name": "IG_SPREAD_WIDEN_50BP", "scenario_type": "CREDIT_SPREAD", "ig": 50.0},
    {"name": "IG_SPREAD_WIDEN_100BP", "scenario_type": "CREDIT_SPREAD", "ig": 100.0},
    {"name": "IG_SPREAD_TIGHTEN_25BP", "scenario_type": "CREDIT_SPREAD", "ig": -25.0},
    {"name": "IG_SPREAD_TIGHTEN_50BP", "scenario_type": "CREDIT_SPREAD", "ig": -50.0},
    {"name": "HY_SPREAD_WIDEN_50BP", "scenario_type": "CREDIT_SPREAD", "hy": 50.0},
    {"name": "HY_SPREAD_WIDEN_100BP", "scenario_type": "CREDIT_SPREAD", "hy": 100.0},
    {"name": "HY_SPREAD_WIDEN_200BP", "scenario_type": "CREDIT_SPREAD", "hy": 200.0},
    {"name": "HY_SPREAD_WIDEN_500BP", "scenario_type": "CREDIT_SPREAD", "hy": 500.0},
    {"name": "HY_SPREAD_TIGHTEN_50BP", "scenario_type": "CREDIT_SPREAD", "hy": -50.0},
    {"name": "HY_SPREAD_TIGHTEN_100BP", "scenario_type": "CREDIT_SPREAD", "hy": -100.0},
    
    # Combined
    {
        "name": "RISK_OFF_MODERATE",
        "scenario_type": "COMBINED",
        "rate_2y_shock_bps": -50.0,
        "rate_5y_shock_bps": -50.0,
        "rate_10y_shock_bps": -50.0,
        "rate_30y_shock_bps": -50.0,
        "ig_spread_shock_bps": 75.0,
        "hy_spread_shock_bps": 150.0
    },
    {
        "name": "RISK_OFF_SEVERE",
        "scenario_type": "COMBINED",
        "rate_2y_shock_bps": -100.0,
        "rate_5y_shock_bps": -100.0,
        "rate_10y_shock_bps": -100.0,
        "rate_30y_shock_bps": -100.0,
        "ig_spread_shock_bps": 150.0,
        "hy_spread_shock_bps": 350.0
    },
    {
        "name": "INFLATION_SHOCK",
        "scenario_type": "COMBINED",
        "rate_2y_shock_bps": 200.0,
        "rate_5y_shock_bps": 175.0,
        "rate_10y_shock_bps": 125.0,
        "rate_30y_shock_bps": 75.0,
        "ig_spread_shock_bps": 50.0,
        "hy_spread_shock_bps": 100.0
    },
    {
        "name": "RAPID_EASING",
        "scenario_type": "COMBINED",
        "rate_2y_shock_bps": -200.0,
        "rate_5y_shock_bps": -150.0,
        "rate_10y_shock_bps": -100.0,
        "rate_30y_shock_bps": -50.0,
        "ig_spread_shock_bps": -25.0,
        "hy_spread_shock_bps": -50.0
    },
    {
        "name": "CREDIT_CRISIS",
        "scenario_type": "COMBINED",
        "rate_2y_shock_bps": -50.0,
        "rate_5y_shock_bps": -50.0,
        "rate_10y_shock_bps": -50.0,
        "rate_30y_shock_bps": -50.0,
        "ig_spread_shock_bps": 250.0,
        "hy_spread_shock_bps": 600.0
    }
]

def seed_scenarios(db: Session):
    for data in SCENARIOS:
        existing = db.query(StressScenario).filter(StressScenario.name == data["name"]).first()
        
        rate_shock = data.get("r", 0.0)
        
        rate_2y = data.get("rate_2y_shock_bps", rate_shock)
        rate_5y = data.get("rate_5y_shock_bps", rate_shock)
        rate_10y = data.get("rate_10y_shock_bps", rate_shock)
        rate_30y = data.get("rate_30y_shock_bps", rate_shock)
        
        ig_spread = data.get("ig", data.get("ig_spread_shock_bps", 0.0))
        hy_spread = data.get("hy", data.get("hy_spread_shock_bps", 0.0))
        
        if existing:
            existing.rate_2y_shock_bps = rate_2y
            existing.rate_5y_shock_bps = rate_5y
            existing.rate_10y_shock_bps = rate_10y
            existing.rate_30y_shock_bps = rate_30y
            existing.ig_spread_shock_bps = ig_spread
            existing.hy_spread_shock_bps = hy_spread
            existing.scenario_type = data["scenario_type"]
            logger.info(f"Updated scenario {data['name']}")
        else:
            scenario = StressScenario(
                name=data["name"],
                description=f"BondGuard pre-defined {data['name']} scenario",
                scenario_type=data["scenario_type"],
                is_predefined=True,
                rate_2y_shock_bps=rate_2y,
                rate_5y_shock_bps=rate_5y,
                rate_10y_shock_bps=rate_10y,
                rate_30y_shock_bps=rate_30y,
                ig_spread_shock_bps=ig_spread,
                hy_spread_shock_bps=hy_spread
            )
            db.add(scenario)
            logger.info(f"Created scenario {data['name']}")
            
    db.commit()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_scenarios(db)
    finally:
        db.close()
