from datetime import date
from decimal import Decimal

import pytest
from app.schemas.bond import BondCreate, BondUpdate
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from app.schemas.transaction import TransactionCreate
from app.services.bond import BondService
from app.services.portfolio import PortfolioService
from app.services.position import PositionService
from sqlalchemy.orm import Session


def test_admin_portfolio_lifecycle(db_session: Session):
    port_svc = PortfolioService(db_session)
    
    # Create active portfolio
    port = port_svc.create_portfolio(PortfolioCreate(name="Admin Port", base_currency="USD"))
    assert port.is_active is True
    assert port.status == "ACTIVE"
    
    # Verify active-only listing
    ports = port_svc.list_portfolios(active_only=True)
    assert any(p.id == port.id for p in ports)
    
    # Update portfolio (Deactivate)
    port_svc.update_portfolio(port.id, PortfolioUpdate(is_active=False, status="INACTIVE"))
    db_session.refresh(port)
    assert port.is_active is False
    assert port.status == "INACTIVE"
    
    # Verify active-only listing excludes it
    ports_active = port_svc.list_portfolios(active_only=True)
    assert not any(p.id == port.id for p in ports_active)
    
    # Safe delete (archival)
    port_svc.delete_portfolio(port.id)
    db_session.refresh(port)
    assert port.is_active is False
    assert port.status == "ARCHIVED"

def test_bond_identifier_and_update_validation(db_session: Session):
    bond_svc = BondService(db_session)
    
    # Test valid ISIN/CUSIP
    bond_data = BondCreate(
        isin="US912828GD97",
        cusip="912828GD9",
        issuer_name="US Treasury",
        bond_name="US Treas 3.125 2030",
        face_value=Decimal('1000.0'),
        coupon_rate=Decimal('0.03125'),
        coupon_frequency="semiannual",
        issue_date=date(2020, 1, 1),
        maturity_date=date(2030, 1, 1),
        day_count_convention="30/360",
        bond_type="GOVERNMENT"
    )
    bond = bond_svc.create_bond(bond_data)
    assert bond.isin == "US912828GD97"
    
    # Test update reference attributes
    update_data = BondUpdate(
        issuer_name="US Govt",
        credit_rating="AA+",
        sector="Sovereign",
        country="US"
    )
    updated = bond_svc.update_bond(bond.id, update_data)
    assert updated.issuer_name == "US Govt"
    assert updated.credit_rating == "AA+"
    assert updated.sector == "Sovereign"
    assert updated.country == "US"

def test_bond_schema_invalid_identifiers():
    from pydantic import ValidationError
    
    # Invalid ISIN (too short)
    with pytest.raises(ValidationError):
        BondCreate(
            isin="US123",
            issuer_name="X", bond_name="Y",
            face_value=Decimal(100), coupon_rate=Decimal('0.05'),
            coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
            day_count_convention="30/360", bond_type="Corp"
        )
        
    # Invalid CUSIP (too long)
    with pytest.raises(ValidationError):
        BondCreate(
            isin="US1234567890",
            cusip="12345678901234",
            issuer_name="X", bond_name="Y",
            face_value=Decimal(100), coupon_rate=Decimal('0.05'),
            coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
            day_count_convention="30/360", bond_type="Corp"
        )

def test_transaction_propagation_and_average_cost(db_session: Session):
    port_svc = PortfolioService(db_session)
    bond_svc = BondService(db_session)
    pos_svc = PositionService(db_session)
    
    port = port_svc.create_portfolio(PortfolioCreate(name="Accounting Port"))
    bond = bond_svc.create_bond(BondCreate(
        isin="US2222222222",
        issuer_name="Issuer B", bond_name="Bond B",
        face_value=Decimal(1000), coupon_rate=Decimal('0.04'),
        coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
        day_count_convention="30/360", bond_type="Corp"
    ))
    
    # BUY 100 bonds at clean price of 98.0
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 1),
        settlement_date=date(2024, 1, 2),
        quantity=Decimal(100),
        clean_price=Decimal('98.0'),
        total_consideration=Decimal('98000.0')
    ))
    
    # BUY another 100 bonds at clean price of 102.0
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 15),
        settlement_date=date(2024, 1, 16),
        quantity=Decimal(100),
        clean_price=Decimal('102.0'),
        total_consideration=Decimal('102000.0')
    ))
    
    from app.db.models import Position
    positions = db_session.query(Position).filter(Position.portfolio_id == port.id).all()
    assert len(positions) == 1
    pos = positions[0]
    
    # Quantity is total face-value units: 200 units
    assert pos.quantity == Decimal(200)
    
    # Average cost: (100 * 98.0 + 100 * 102.0) / 200 = 100.0
    assert pos.average_cost == Decimal('100.0')
