
from app.db.models import Bond
from app.schemas.bond import BondCreate, BondUpdate
from sqlalchemy.orm import Session


class BondService:
    def __init__(self, db: Session):
        self.db = db

    def create_bond(self, schema: BondCreate) -> Bond:
        bond = Bond(**schema.model_dump())
        self.db.add(bond)
        self.db.commit()
        self.db.refresh(bond)
        return bond

    def get_bond(self, bond_id: int) -> Bond | None:
        return self.db.query(Bond).filter(Bond.id == bond_id).first()

    def search_bonds(self, issuer: str | None = None, rating: str | None = None, 
                     sector: str | None = None, maturity_from: str | None = None, 
                     maturity_to: str | None = None) -> list[Bond]:
        query = self.db.query(Bond)
        if issuer:
            query = query.filter(Bond.issuer_name.ilike(f"%{issuer}%"))
        if rating:
            query = query.filter(Bond.credit_rating == rating)
        if sector:
            query = query.filter(Bond.sector == sector)
        if maturity_from:
            query = query.filter(Bond.maturity_date >= maturity_from)
        if maturity_to:
            query = query.filter(Bond.maturity_date <= maturity_to)
        return query.all()

    def update_bond(self, bond_id: int, schema: BondUpdate) -> Bond | None:
        bond = self.get_bond(bond_id)
        if not bond:
            return None
        update_data = schema.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(bond, k, v)
        self.db.commit()
        self.db.refresh(bond)
        return bond
