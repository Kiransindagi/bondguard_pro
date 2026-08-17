from datetime import date

from app.db.database import SessionLocal
from app.db.models import RiskLimit


def seed_limits(db=None):
    is_local = False
    if db is None:
        db = SessionLocal()
        is_local = True
    try:
        limits = [
            {
                'code': 'L-DUR-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Maximum Modified Duration',
                'description': 'Portfolio modified duration must not exceed 8 years',
                'metric_type': 'PORTFOLIO_MODIFIED_DURATION',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 7.0,
                'limit_threshold': 8.0,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-DV01-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Maximum DV01',
                'description': 'Total DV01 must not exceed 100,000',
                'metric_type': 'TOTAL_DV01',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 80000.0,
                'limit_threshold': 100000.0,
                'severity': 'SOFT_LIMIT'
            },
            {
                'code': 'L-VAR-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Maximum VaR',
                'description': 'Historical VaR (95%) must not exceed 50,000',
                'metric_type': 'HISTORICAL_VAR_95_1D',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 40000.0,
                'limit_threshold': 50000.0,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-STRESS-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Worst Stress Loss',
                'description': 'Loss under worst stress scenario must not exceed 100,000',
                'metric_type': 'WORST_STRESS_LOSS',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 80000.0,
                'limit_threshold': 100000.0,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-ISS-CONC-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Issuer Concentration',
                'description': 'Maximum exposure to single issuer must not exceed 15%',
                'metric_type': 'ISSUER_CONCENTRATION_MAX',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 0.10,
                'limit_threshold': 0.15,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-SEC-CONC-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Sector Concentration',
                'description': 'Maximum exposure to single sector must not exceed 30%',
                'metric_type': 'SECTOR_CONCENTRATION_MAX',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 0.25,
                'limit_threshold': 0.30,
                'severity': 'SOFT_LIMIT'
            },
            {
                'code': 'L-LIQ-MIN',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Minimum Liquidity Score',
                'description': 'Portfolio liquidity score must be at least 70',
                'metric_type': 'LIQUIDITY_SCORE',
                'scope_type': 'GLOBAL',
                'direction': 'MINIMUM',
                'warning_threshold': 75.0,
                'limit_threshold': 70.0,
                'severity': 'SOFT_LIMIT'
            },
            {
                'code': 'L-LIQ-COST-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Max Liquidation Cost',
                'description': 'Liquidation cost must not exceed 25 bps',
                'metric_type': 'LIQUIDATION_COST_BPS',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 20.0,
                'limit_threshold': 25.0,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-LIQ-DAYS-MAX',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Max Days to Liquidate',
                'description': 'Weighted days to liquidate must not exceed 5',
                'metric_type': 'MAX_DAYS_TO_LIQUIDATE',
                'scope_type': 'GLOBAL',
                'direction': 'MAXIMUM',
                'warning_threshold': 3.0,
                'limit_threshold': 5.0,
                'severity': 'HARD_LIMIT'
            },
            {
                'code': 'L-DUR-MAX-P1',
                'name': 'DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT - Max Modified Duration (Portfolio Override)',
                'description': 'Portfolio 1 modified duration must not exceed 6 years',
                'metric_type': 'PORTFOLIO_MODIFIED_DURATION',
                'scope_type': 'PORTFOLIO',
                'scope_value': '1',
                'direction': 'MAXIMUM',
                'warning_threshold': 5.0,
                'limit_threshold': 6.0,
                'severity': 'HARD_LIMIT'
            }
        ]
        
        for limit_dict in limits:
            existing = db.query(RiskLimit).filter(RiskLimit.code == limit_dict['code']).first()
            if not existing:
                lim = RiskLimit(
                    code=limit_dict['code'],
                    name=limit_dict['name'],
                    description=limit_dict['description'],
                    metric_type=limit_dict['metric_type'],
                    scope_type=limit_dict['scope_type'],
                    scope_value=limit_dict.get('scope_value'),
                    direction=limit_dict['direction'],
                    warning_threshold=limit_dict['warning_threshold'],
                    limit_threshold=limit_dict['limit_threshold'],
                    severity=limit_dict['severity'],
                    effective_from=date(2020, 1, 1),
                    is_active=True
                )
                db.add(lim)
        
        db.commit()
        print("Seeded demonstration risk limits.")
    finally:
        if is_local:
            db.close()

if __name__ == "__main__":
    seed_limits()
