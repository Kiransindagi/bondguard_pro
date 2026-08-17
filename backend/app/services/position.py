from decimal import Decimal

from app.db.models import Bond, Position, Transaction
from app.schemas.transaction import TransactionCreate
from fastapi import HTTPException
from sqlalchemy.orm import Session


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

        qty = schema.quantity
        clean_price = schema.clean_price

        if not position:
            if schema.transaction_type == "SELL":
                raise HTTPException(status_code=400, detail="Cannot SELL without an existing position")
            position = Position(
                portfolio_id=schema.portfolio_id,
                bond_id=schema.bond_id,
                quantity=Decimal(0),
                average_cost=Decimal(0)
            )
            self.db.add(position)

        if schema.transaction_type == "BUY":
            new_total_qty = position.quantity + qty
            new_cost = ((position.quantity * position.average_cost) + (qty * clean_price)) / new_total_qty
            position.quantity = new_total_qty
            position.average_cost = new_cost
        elif schema.transaction_type == "SELL":
            if position.quantity < qty:
                raise HTTPException(status_code=400, detail="Overselling is not allowed")
            position.quantity -= qty
        elif schema.transaction_type == "ADJUSTMENT":
            new_total_qty = position.quantity + qty
            if new_total_qty < 0:
                raise HTTPException(status_code=400, detail="Position quantity cannot be negative after adjustment")
            position.quantity = new_total_qty
            if clean_price is not None:
                position.average_cost = clean_price

        position.current_clean_price = clean_price
        if position.quantity > 0:
            position.market_value = (position.quantity * bond.face_value * position.current_clean_price) / Decimal('100.0')
            cost_basis = (position.quantity * bond.face_value * position.average_cost) / Decimal('100.0')
            position.unrealized_pnl = position.market_value - cost_basis
        else:
            position.market_value = Decimal(0)
            position.unrealized_pnl = Decimal(0)

        trade_date = schema.trade_date
        settlement_date = schema.settlement_date or trade_date
        accrued_interest = schema.accrued_interest or Decimal('0.0')
        total_consideration = schema.total_consideration
        if total_consideration is None:
            total_consideration = (abs(qty) * bond.face_value * clean_price) / Decimal('100.0') + accrued_interest

        txn = Transaction(
            portfolio_id=schema.portfolio_id,
            bond_id=schema.bond_id,
            transaction_type=schema.transaction_type,
            trade_date=trade_date,
            settlement_date=settlement_date,
            quantity=qty,
            clean_price=clean_price,
            accrued_interest=accrued_interest,
            total_consideration=total_consideration
        )
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def reconcile_portfolio_positions(self, portfolio_id: int) -> bool:
        txs = self.db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).order_by(Transaction.trade_date.asc(), Transaction.id.asc()).all()
        expected_qtys = {}
        expected_costs = {}
        
        for tx in txs:
            b_id = tx.bond_id
            if b_id not in expected_qtys:
                expected_qtys[b_id] = Decimal(0)
                expected_costs[b_id] = Decimal(0)
                
            qty = tx.quantity
            price = tx.clean_price
            
            if tx.transaction_type == "BUY":
                new_qty = expected_qtys[b_id] + qty
                if new_qty > 0:
                    expected_costs[b_id] = ((expected_qtys[b_id] * expected_costs[b_id]) + (qty * price)) / new_qty
                expected_qtys[b_id] = new_qty
            elif tx.transaction_type == "SELL":
                expected_qtys[b_id] = max(Decimal(0), expected_qtys[b_id] - qty)
            elif tx.transaction_type == "ADJUSTMENT":
                expected_qtys[b_id] = max(Decimal(0), expected_qtys[b_id] + qty)
                if price > 0:
                    expected_costs[b_id] = price

        positions = self.db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
        positions_map = {p.bond_id: p for p in positions}
        reconciled = True
        
        for b_id, req_qty in expected_qtys.items():
            bond = self.db.query(Bond).filter(Bond.id == b_id).first()
            if not bond:
                continue
            pos = positions_map.get(b_id)
            if not pos:
                pos = Position(
                    portfolio_id=portfolio_id,
                    bond_id=b_id,
                    quantity=Decimal(0),
                    average_cost=Decimal(0),
                    current_clean_price=expected_costs[b_id] if expected_costs[b_id] > 0 else Decimal('100.0')
                )
                self.db.add(pos)
                reconciled = False
            
            if pos.quantity != req_qty or pos.average_cost != expected_costs[b_id]:
                pos.quantity = req_qty
                pos.average_cost = expected_costs[b_id]
                reconciled = False
                
            if pos.current_clean_price is None:
                pos.current_clean_price = pos.average_cost if pos.average_cost > 0 else Decimal('100.0')
                
            if pos.quantity > 0:
                pos.market_value = (pos.quantity * bond.face_value * pos.current_clean_price) / Decimal('100.0')
                cost_basis = (pos.quantity * bond.face_value * pos.average_cost) / Decimal('100.0')
                pos.unrealized_pnl = pos.market_value - cost_basis
            else:
                pos.market_value = Decimal(0)
                pos.unrealized_pnl = Decimal(0)
                
        for b_id, pos in positions_map.items():
            if b_id not in expected_qtys and pos.quantity != 0:
                pos.quantity = Decimal(0)
                pos.market_value = Decimal(0)
                pos.unrealized_pnl = Decimal(0)
                reconciled = False
                    
        self.db.commit()
        return reconciled
