from app.db.database import SessionLocal
from app.db.models import Portfolio, Bond, Transaction, Position
from datetime import date
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        # 1. Get or Create Portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.name == "Global Core Fixed Income").first()
        if not portfolio:
            portfolio = Portfolio(
                name="Global Core Fixed Income",
                description="Demonstration portfolio for BondGuard Pro",
                base_currency="USD",
                benchmark="Bloomberg Global Aggregate"
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            logger.info(f"Created portfolio: {portfolio.name}")
        else:
            logger.info(f"Portfolio {portfolio.name} already exists.")

        # 2. Upsert Bonds (Synthetic)
        bonds_data = [
            {
                "isin": "US91282CDJ71",
                "ticker": "T 4.5 11/30/35",
                "issuer_name": "US Treasury",
                "bond_name": "US Treasury Note 4.5% 2035 (Synthetic)",
                "face_value": Decimal('100.00'),
                "coupon_rate": Decimal('0.045'),
                "coupon_frequency": "semiannual",
                "issue_date": date(2023, 11, 30),
                "maturity_date": date(2035, 11, 30),
                "day_count_convention": "ACT/ACT",
                "bond_type": "Government",
                "credit_rating": "AA+",
                "sector": "Treasury",
                "country": "USA"
            },
            {
                "isin": "US037833EC51",
                "ticker": "AAPL 3.85 05/04/43",
                "issuer_name": "Apple Inc.",
                "bond_name": "Apple Inc. 3.85% 2043 (Synthetic)",
                "face_value": Decimal('100.00'),
                "coupon_rate": Decimal('0.0385'),
                "coupon_frequency": "semiannual",
                "issue_date": date(2013, 5, 4),
                "maturity_date": date(2043, 5, 4),
                "day_count_convention": "30/360",
                "bond_type": "Corporate",
                "credit_rating": "AA+",
                "sector": "Technology",
                "country": "USA"
            },
            {
                "isin": "US345370CZ16",
                "ticker": "F 3.25 02/12/32",
                "issuer_name": "Ford Motor Credit",
                "bond_name": "Ford Motor Credit 3.25% 2032 (Synthetic)",
                "face_value": Decimal('100.00'),
                "coupon_rate": Decimal('0.0325'),
                "coupon_frequency": "semiannual",
                "issue_date": date(2022, 2, 12),
                "maturity_date": date(2032, 2, 12),
                "day_count_convention": "30/360",
                "bond_type": "Corporate",
                "credit_rating": "BB+",
                "sector": "Consumer",
                "country": "USA"
            },
            {
                "isin": "XS2345678912",
                "ticker": "PETBRA 5.6 01/03/31",
                "issuer_name": "Petrobras",
                "bond_name": "Petrobras 5.6% 2031 (Synthetic)",
                "face_value": Decimal('100.00'),
                "coupon_rate": Decimal('0.056'),
                "coupon_frequency": "semiannual",
                "issue_date": date(2021, 1, 3),
                "maturity_date": date(2031, 1, 3),
                "day_count_convention": "30/360",
                "bond_type": "Corporate",
                "credit_rating": "BB-",
                "sector": "Energy",
                "country": "Brazil"
            }
        ]

        bonds = []
        for bd in bonds_data:
            bond = db.query(Bond).filter(Bond.isin == bd["isin"]).first()
            if not bond:
                bond = Bond(**bd)
                db.add(bond)
            else:
                for k, v in bd.items():
                    setattr(bond, k, v)
            bonds.append(bond)
        
        db.commit()
        for bond in bonds:
            db.refresh(bond)
        logger.info(f"Upserted {len(bonds)} synthetic bonds.")

        # 3. Get or Create Transactions (which creates positions)
        from app.services.position import PositionService
        from app.schemas.transaction import TransactionCreate
        
        pos_service = PositionService(db)

        # Check if transactions already exist for this portfolio
        existing_txns = db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id).count()
        if existing_txns == 0:
            # Note: total_consideration = quantity * face_value * clean_price / 100
            transactions_data = [
                # Buy Treasury
                TransactionCreate(
                    portfolio_id=portfolio.id,
                    bond_id=bonds[0].id,
                    transaction_type="BUY",
                    trade_date=date(2024, 1, 15),
                    settlement_date=date(2024, 1, 16),
                    quantity=Decimal('10000'),
                    clean_price=Decimal('99.50'),
                    accrued_interest=Decimal('0.0'),
                    total_consideration=Decimal('10000') * Decimal('100.00') * Decimal('99.50') / Decimal('100')
                ),
                # Buy IG Corporate
                TransactionCreate(
                    portfolio_id=portfolio.id,
                    bond_id=bonds[1].id,
                    transaction_type="BUY",
                    trade_date=date(2024, 1, 20),
                    settlement_date=date(2024, 1, 22),
                    quantity=Decimal('5000'),
                    clean_price=Decimal('95.20'),
                    accrued_interest=Decimal('0.0'),
                    total_consideration=Decimal('5000') * Decimal('100.00') * Decimal('95.20') / Decimal('100')
                ),
                # Buy HY Corporate
                TransactionCreate(
                    portfolio_id=portfolio.id,
                    bond_id=bonds[2].id,
                    transaction_type="BUY",
                    trade_date=date(2024, 2, 1),
                    settlement_date=date(2024, 2, 3),
                    quantity=Decimal('8000'),
                    clean_price=Decimal('88.75'),
                    accrued_interest=Decimal('0.0'),
                    total_consideration=Decimal('8000') * Decimal('100.00') * Decimal('88.75') / Decimal('100')
                ),
                # Buy EM Debt
                TransactionCreate(
                    portfolio_id=portfolio.id,
                    bond_id=bonds[3].id,
                    transaction_type="BUY",
                    trade_date=date(2024, 2, 10),
                    settlement_date=date(2024, 2, 12),
                    quantity=Decimal('4000'),
                    clean_price=Decimal('102.10'),
                    accrued_interest=Decimal('0.0'),
                    total_consideration=Decimal('4000') * Decimal('100.00') * Decimal('102.10') / Decimal('100')
                )
            ]

            for tx_data in transactions_data:
                pos_service.execute_transaction(tx_data)
            
            logger.info(f"Created {len(transactions_data)} initial transactions.")
        else:
            logger.info(f"Transactions already exist. Skipped transaction seeding.")

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_data()
