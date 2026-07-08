from .types import LiquidityAssumptionConfig

def _get_type_score(bond_type: str) -> float:
    t = bond_type.upper()
    if 'TREASURY' in t or 'GOVERNMENT' in t:
        return 100.0
    elif 'AGENCY' in t:
        return 90.0
    elif 'CORPORATE' in t:
        return 70.0
    else:
        return 50.0

def _get_rating_score(rating: str) -> float:
    if not rating:
        return 50.0
    r = rating.upper()
    if r in ['AAA', 'AA+', 'AA', 'AA-']:
        return 100.0
    elif r in ['A+', 'A', 'A-']:
        return 85.0
    elif r in ['BBB+', 'BBB', 'BBB-']:
        return 70.0
    elif r in ['BB+', 'BB', 'BB-']:
        return 50.0
    elif r in ['B+', 'B', 'B-']:
        return 30.0
    else:
        return 10.0

def _get_maturity_score(years_to_maturity: float) -> float:
    if years_to_maturity <= 2:
        return 100.0
    elif years_to_maturity <= 5:
        return 90.0
    elif years_to_maturity <= 10:
        return 80.0
    elif years_to_maturity <= 20:
        return 60.0
    else:
        return 40.0

def _get_concentration_score(weight: float) -> float:
    if weight <= 0.05:
        return 100.0
    elif weight <= 0.10:
        return 80.0
    elif weight <= 0.20:
        return 60.0
    else:
        return 30.0

def calculate_liquidity_score(bond_type: str, rating: str, years_to_maturity: float, weight: float, config: LiquidityAssumptionConfig) -> float:
    s_type = _get_type_score(bond_type)
    s_rating = _get_rating_score(rating)
    s_mat = _get_maturity_score(years_to_maturity)
    s_conc = _get_concentration_score(weight)

    score = (s_type * config.weight_type +
             s_rating * config.weight_rating +
             s_mat * config.weight_maturity +
             s_conc * config.weight_concentration)
    return min(max(score, 0.0), 100.0)
