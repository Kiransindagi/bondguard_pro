from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.schemas.bond import BondCreate, BondResponse
from app.services.bond import BondService
from sqlalchemy.exc import IntegrityError
from app.auth.dependencies import PermissionChecker
from app.auth.permissions import PORTFOLIO_READ, PORTFOLIO_WRITE

router = APIRouter()

@router.post("", response_model=BondResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def create_bond(schema: BondCreate, db: Session = Depends(get_db)):
    svc = BondService(db)
    try:
        return svc.create_bond(schema)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Bond ISIN or CUSIP already exists")

@router.get("", response_model=List[BondResponse], dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def list_bonds(
    issuer: Optional[str] = None,
    rating: Optional[str] = None,
    sector: Optional[str] = None,
    maturity_from: Optional[str] = None,
    maturity_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    svc = BondService(db)
    return svc.search_bonds(issuer, rating, sector, maturity_from, maturity_to)

@router.get("/{bond_id}", response_model=BondResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_bond(bond_id: int, db: Session = Depends(get_db)):
    svc = BondService(db)
    bond = svc.get_bond(bond_id)
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    return bond

