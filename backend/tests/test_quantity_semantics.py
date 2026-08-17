from datetime import date
from decimal import Decimal

from app.schemas.bond import BondCreate
from app.schemas.portfolio import PortfolioCreate
from app.schemas.transaction import TransactionCreate
from app.services.bond import BondService
from app.services.portfolio import PortfolioService
from app.services.position import PositionService


def test_quantity_market_value_convention(db_session):
    port_svc = PortfolioService(db_session)
    bond_svc = BondService(db_session)
    pos_svc = PositionService(db_session)

    port = port_svc.create_portfolio(PortfolioCreate(name="Semantics Port"))
    
    # Bond with face value 1000
    bond1 = bond_svc.create_bond(BondCreate(
        isin="US9999999991",
        issuer_name="T1", bond_name="T1 Bond",
        face_value=Decimal(1000), coupon_rate=Decimal('0.05'),
        coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
        day_count_convention="30/360", bond_type="Corp"
    ))

    # Bond with face value 100
    bond2 = bond_svc.create_bond(BondCreate(
        isin="US9999999992",
        issuer_name="T2", bond_name="T2 Bond",
        face_value=Decimal(100), coupon_rate=Decimal('0.05'),
        coupon_frequency="annual", issue_date=date(2020,1,1), maturity_date=date(2030,1,1),
        day_count_convention="30/360", bond_type="Corp"
    ))

    # Buy 10 units of bond1 (face value 1000) at 99.5
    # Total Consideration = 10 * 1000 * 99.5 / 100 = 9950.0
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond1.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 1),
        settlement_date=date(2024, 1, 2),
        quantity=Decimal(10),
        clean_price=Decimal('99.50'),
        total_consideration=Decimal('9950.0')
    ))

    # Buy 10000 units of bond2 (face value 100) at 99.5
    # Total Consideration = 10000 * 100 * 99.5 / 100 = 995000.0
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond2.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 1),
        settlement_date=date(2024, 1, 2),
        quantity=Decimal(10000),
        clean_price=Decimal('99.50'),
        total_consideration=Decimal('995000.0')
    ))

    summary = port_svc.get_portfolio_summary(port.id)
    assert summary["total_market_value"] == Decimal('9950.0') + Decimal('995000.0')
    assert summary["total_unrealized_pnl"] == Decimal('0.0')

    # Price goes up to 100.0 for bond1
    pos_svc.execute_transaction(TransactionCreate(
        portfolio_id=port.id,
        bond_id=bond1.id,
        transaction_type="BUY",
        trade_date=date(2024, 1, 5),
        settlement_date=date(2024, 1, 6),
        quantity=Decimal(10),
        clean_price=Decimal('100.00'),
        total_consideration=Decimal('10000.0') # 10 * 1000 * 100 / 100 = 10000
    ))

    # Now average cost for bond1 is (99.5 * 10 + 100.0 * 10) / 20 = 99.75
    # Quantity = 20
    # New clean price = 100.0
    # Market Value for bond1 = 20 * 1000 * 100.0 / 100 = 20000.0
    # Cost basis = 20 * 1000 * 99.75 / 100 = 19950.0
    # Unrealized P&L for bond1 = 20000.0 - 19950.0 = 50.0
    
    summary2 = port_svc.get_portfolio_summary(port.id)
    assert summary2["total_market_value"] == Decimal('20000.0') + Decimal('995000.0')
    assert summary2["total_unrealized_pnl"] == Decimal('50.0')
