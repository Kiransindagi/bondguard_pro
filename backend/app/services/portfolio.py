from decimal import Decimal

from app.db.models import Portfolio, Position
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from sqlalchemy.orm import Session


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, schema: PortfolioCreate) -> Portfolio:
        port = Portfolio(**schema.model_dump())
        self.db.add(port)
        self.db.commit()
        self.db.refresh(port)
        return port

    def get_portfolio(self, portfolio_id: int) -> Portfolio | None:
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def list_portfolios(self, active_only: bool = False) -> list[Portfolio]:
        query = self.db.query(Portfolio)
        if active_only:
            query = query.filter(Portfolio.is_active == True, Portfolio.status == "ACTIVE")
        return query.all()

    def update_portfolio(self, portfolio_id: int, schema: PortfolioUpdate) -> Portfolio | None:
        port = self.get_portfolio(portfolio_id)
        if not port:
            return None
        update_data = schema.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(port, k, v)
        self.db.commit()
        self.db.refresh(port)
        return port

    def delete_portfolio(self, portfolio_id: int) -> bool:
        port = self.get_portfolio(portfolio_id)
        if not port:
            return False
        port.is_active = False
        port.status = "ARCHIVED"
        self.db.commit()
        return True

    def get_portfolio_summary(self, portfolio_id: int):
        port = self.get_portfolio(portfolio_id)
        if not port:
            return None
        
        positions = self.db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
        tmv = sum([p.market_value for p in positions if p.market_value], Decimal(0))
        tpnl = sum([p.unrealized_pnl for p in positions if p.unrealized_pnl], Decimal(0))
        
        return {
            "id": port.id,
            "name": port.name,
            "description": port.description,
            "base_currency": port.base_currency,
            "benchmark": port.benchmark,
            "created_at": port.created_at,
            "updated_at": port.updated_at,
            "total_market_value": tmv,
            "total_unrealized_pnl": tpnl,
            "position_count": len(positions)
        }
