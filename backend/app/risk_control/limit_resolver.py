from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import or_
from app.db.models import RiskLimit

class LimitResolver:
    @staticmethod
    def resolve_applicable_limits(db: Session, portfolio_id: int, valuation_date: date) -> List[RiskLimit]:
        # Exclude inactive, future-effective, and expired limits based on valuation_date
        limits = db.query(RiskLimit).filter(
            RiskLimit.is_active.is_(True),
            RiskLimit.effective_from <= valuation_date,
            or_(RiskLimit.effective_to.is_(None), RiskLimit.effective_to >= valuation_date)
        ).all()
        
        # Precedence: PORTFOLIO > matching scope-specific > GLOBAL
        # Current support: PORTFOLIO and GLOBAL only for Phase B
        resolved: Dict[str, RiskLimit] = {}
        
        for limit in limits:
            if limit.scope_type == 'GLOBAL':
                if limit.metric_type not in resolved or resolved[limit.metric_type].scope_type == 'GLOBAL':
                    resolved[limit.metric_type] = limit
            elif limit.scope_type == 'PORTFOLIO' and limit.scope_value == str(portfolio_id):
                # Always overwrite GLOBAL
                resolved[limit.metric_type] = limit
                
        return list(resolved.values())
