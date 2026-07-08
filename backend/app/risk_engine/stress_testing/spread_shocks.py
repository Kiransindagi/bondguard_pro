from app.db.models import Bond

def resolve_spread_shock(bond: Bond, ig_shock_bps: float, hy_shock_bps: float) -> float:
    """
    Resolve the applicable credit spread shock for a bond.
    Treasury positions receive 0.0 bps shock.
    Corporate positions receive IG or HY shock based on rating/mapping.
    """
    if bond.bond_type != "Corporate":
        return 0.0
        
    rating = getattr(bond, "credit_rating", "")
    if not rating:
        return ig_shock_bps # default to IG if unknown
        
    hy_ratings = ["BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
    if rating.upper() in hy_ratings or ("Petrobras" in (bond.bond_name or "")):
        return hy_shock_bps
        
    return ig_shock_bps
