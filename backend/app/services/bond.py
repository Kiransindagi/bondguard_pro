from sqlalchemy.orm import Session
from app.db.models import Bond
from app.schemas.bond import BondCreate, BondUpdate
from typing import List, Optional

class BondService:
    def __init__(self, db: Session):
        self.db = db

    def create_bond(self, schema: BondCreate) -> Bond:
        bond = Bond(**schema.model_dump())
        self.db.add(bond)
        self.db.commit()
        self.db.refresh(bond)
        return bond

    def get_bond(self, bond_id: int) -> Optional[Bond]:
        return self.db.query(Bond).filter(Bond.id == bond_id).first()

    def search_bonds(self, issuer: Optional[str] = None, rating: Optional[str] = None, 
                     sector: Optional[str] = None, maturity_from: Optional[str] = None, 
                     maturity_to: Optional[str] = None) -> List[Bond]:
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

    def update_bond(self, bond_id: int, schema: BondUpdate) -> Optional[Bond]:
        bond = self.get_bond(bond_id)
        if not bond:
            return None
        update_data = schema.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(bond, k, v)
        self.db.commit()
        self.db.refresh(bond)
        return bond
