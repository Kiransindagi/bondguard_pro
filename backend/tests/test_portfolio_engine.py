from datetime import date
from decimal import Decimal

import pytest
from app.schemas.bond import BondCreate
from app.schemas.portfolio import PortfolioCreate
from app.schemas.transaction import TransactionCreate
from app.services.bond import BondService
from app.services.bond_pricing import (
    calculate_accrued_interest,
    calculate_cash_flows,
    clean_to_dirty_price,
    dirty_to_clean_price,
    generate_coupon_schedule,
)
from app.services.portfolio import PortfolioService
from app.services.position import PositionService
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def test_portfolio_crud(db_session):
    svc = PortfolioService(db_session)
    port = svc.create_portfolio(PortfolioCreate(name="Test Port", base_currency="USD"))
    assert port.id is not None
    assert port.name == "Test Port"

    ports = svc.list_portfolios()
    assert len(ports) == 1

    summary = svc.get_portfolio_summary(port.id)
    assert summary["total_market_value"] == Decimal(0)

def test_bond_validation_and_duplicate(db_session):
    svc = BondService(db_session)
    bond_data = BondCreate(
        isin="US1234567890",
        issuer_name="Test Issuer",
        bond_name="Test Bond",
        face_value=Decimal('100.0'),
        coupon_rate=Decimal('0.05'),
        coupon_frequency="semiannual",
        issue_date=date(2020, 1, 1),
        maturity_date=date(2030, 1, 1),
        day_count_convention="30/360",
        bond_type="Corporate"
    )
    bond = svc.create_bond(bond_data)
    assert bond.id is not None

    # Test Duplicate ISIN rejection
    with pytest.raises(IntegrityError):
        svc.create_bond(bond_data)
    db_session.rollback()

    # Test Maturity Validation
    with pytest.raises(ValueError):
        BondCreate(
            isin="US0987654321",
            issuer_name="Test",
            bond_name="Test",
            face_value=Decimal('100.0'),
            coupon_rate=Decimal('0.05'),
            coupon_frequency="annual",
            issue_date=date(2030, 1, 1),
            maturity_date=date(2020, 1, 1), # Invalid
            day_count_convention="ACT/ACT",
            bond_type="Government"
        )

def test_transaction_position_accounting(db_session):
    port_svc = PortfolioService(db_session)
    bond_svc = BondService(db_session)
    pos_svc = PositionService(db_session)

    port = port_svc.create_portfolio(PortfolioCreate(name="Trx Port"))
    bond = bond_svc.create_bond(BondCreate(
        isin="US1111111111",
        issuer_name="A", bond_name="B",
        face_value=Decimal(1000), coupon_rate=Decimal('0.05'),
        coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
        day_count_convention="30/360", bond_type="Corp"
    ))

    # Buy 1
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 1),
        settlement_date=date(2024, 1, 2),
        quantity=Decimal(100),
        clean_price=Decimal('100.0'),
        total_consideration=Decimal('100000.0')
    ))

    summary = port_svc.get_portfolio_summary(port.id)
    assert summary["position_count"] == 1
    # 100 * 1000 * 100 / 100 = 100000
    assert summary["total_market_value"] == Decimal('100000.0')
    
    # Buy 2 (Higher Price -> tests weighted average cost)
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id, bond_id=bond.id, transaction_type="BUY",
        trade_date=date(2024, 1, 5), settlement_date=date(2024, 1, 6),
        quantity=Decimal(100), clean_price=Decimal('110.0'), total_consideration=Decimal('110000.0')
    ))

    # Average cost should be 105.0. New current price 110.0. Market Value = 200 * 1000 * 110 / 100 = 220000
    # Unrealized PNL = 220000 - (200 * 1000 * 105 / 100) = 220000 - 210000 = 10000
    summary2 = port_svc.get_portfolio_summary(port.id)
    assert summary2["total_market_value"] == Decimal('220000.0')
    assert summary2["total_unrealized_pnl"] == Decimal('10000.0')

    # Sell half
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id, bond_id=bond.id, transaction_type="SELL",
        trade_date=date(2024, 1, 10), settlement_date=date(2024, 1, 11),
        quantity=Decimal(100), clean_price=Decimal('115.0'), total_consideration=Decimal('115000.0')
    ))

    # Left with 100 qty, cost basis still 105.0. Current price 115.0. Market Value = 100 * 1000 * 115 / 100 = 115000
    # PNL = 115000 - (100 * 1000 * 105 / 100) = 115000 - 105000 = 10000
    summary3 = port_svc.get_portfolio_summary(port.id)
    assert summary3["total_market_value"] == Decimal('115000.0')
    assert summary3["total_unrealized_pnl"] == Decimal('10000.0')

    # Overselling should fail
    with pytest.raises(HTTPException) as exc:
        pos_svc.execute_transaction(TransactionCreate(
            portfolio_id=port.id, bond_id=bond.id, transaction_type="SELL",
            trade_date=date(2024, 1, 15), settlement_date=date(2024, 1, 16),
            quantity=Decimal(200), clean_price=Decimal('115.0'), total_consideration=Decimal('23000.0')
        ))
    assert exc.value.status_code == 400

def test_bond_pricing_functions():
    issue = date(2023, 1, 1)
    maturity = date(2026, 1, 1)
    
    schedule = generate_coupon_schedule(issue, maturity, "annual")
    assert schedule == [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1)]

    cash_flows = calculate_cash_flows(Decimal(100), Decimal('0.05'), "annual", schedule)
    assert len(cash_flows) == 3
    assert cash_flows[0][1] == Decimal(5)
    assert cash_flows[1][1] == Decimal(5)
    assert cash_flows[2][1] == Decimal(105)

    # Accrued Interest Test 30/360
    settle = date(2024, 7, 1) # Half a year past Jan 1, 2024
    ai = calculate_accrued_interest(settle, issue, schedule, Decimal(100), Decimal('0.05'), "30/360")
    # 6 months = 180 days / 360 = 0.5 * 5 = 2.5
    assert ai == Decimal('2.5')

    clean = Decimal('98.5')
    dirty = clean_to_dirty_price(clean, ai)
    assert dirty == Decimal('101.0')
    assert dirty_to_clean_price(dirty, ai) == clean
