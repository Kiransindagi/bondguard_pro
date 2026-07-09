from scripts.seed.seed_portfolio import seed_data
from app.db.models import Bond, Portfolio, Transaction
from datetime import date

def test_seed_script_idempotency_and_treasury_maturity(db_session):
    # First run
    seed_data(db_session)
    
    # Check treasury bond
    treasury = db_session.query(Bond).filter(Bond.isin == "US91282CDJ71").first()
    assert treasury is not None
    assert treasury.maturity_date == date(2035, 11, 30)

    # Check portfolio and transaction counts
    portfolio_count = db_session.query(Portfolio).count()
    tx_count = db_session.query(Transaction).count()
    bond_count = db_session.query(Bond).count()

    # Second run should be idempotent
    seed_data(db_session)

    assert db_session.query(Portfolio).count() == portfolio_count
    assert db_session.query(Transaction).count() == tx_count
    assert db_session.query(Bond).count() == bond_count
