from sqlalchemy.orm import Session
from decimal import Decimal
from app.db.models import Position, Transaction, Bond
from app.schemas.transaction import TransactionCreate
from fastapi import HTTPException

class PositionService:
    def __init__(self, db: Session):
        self.db = db

    def execute_transaction(self, schema: TransactionCreate) -> Transaction:
        bond = self.db.query(Bond).filter(Bond.id == schema.bond_id).first()
        if not bond:
            raise HTTPException(status_code=404, detail="Bond not found")
        
        position = self.db.query(Position).filter(
            Position.portfolio_id == schema.portfolio_id,
            Position.bond_id == schema.bond_id
        ).with_for_update().first()

        if not position:
            if schema.transaction_type == "SELL":
                raise HTTPException(status_code=400, detail="Cannot SELL without an existing position")
            position = Position(
                portfolio_id=schema.portfolio_id,
                bond_id=schema.bond_id,
                quantity=Decimal('0'),
                average_cost=Decimal('0')
            )
            self.db.add(position)

        qty = schema.quantity
        clean_price = schema.clean_price

        if schema.transaction_type == "BUY":
            # Weighted average cost: (Current Qty * Current Avg Cost) + (New Qty * New Clean Price) / (Current Qty + New Qty)
            new_total_qty = position.quantity + qty
            new_cost = ((position.quantity * position.average_cost) + (qty * clean_price)) / new_total_qty
            
            position.quantity = new_total_qty
            position.average_cost = new_cost
        elif schema.transaction_type == "SELL":
            if position.quantity < qty:
                raise HTTPException(status_code=400, detail="Overselling is not allowed")
            position.quantity -= qty
            # Average cost remains the same on SELL

        # Always update current clean price and recalculate market value
        position.current_clean_price = clean_price
        if position.quantity > 0:
            # market_value = quantity * face_value * clean_price / 100
            position.market_value = (position.quantity * bond.face_value * position.current_clean_price) / Decimal('100.0')
            cost_basis = (position.quantity * bond.face_value * position.average_cost) / Decimal('100.0')
            position.unrealized_pnl = position.market_value - cost_basis
        else:
            position.market_value = Decimal('0')
            position.unrealized_pnl = Decimal('0')

        txn = Transaction(**schema.model_dump())
        self.db.add(txn)
        
        self.db.commit()
        self.db.refresh(txn)
        return txn
