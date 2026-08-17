from .types import StressScenarioType


def get_stressed_multipliers(scenario: StressScenarioType, bond_type: str) -> (float, float):
    """Returns (spread_multiplier, capacity_multiplier)"""
    if scenario == StressScenarioType.NORMAL:
        return 1.0, 1.0
    
    t = bond_type.upper()
    is_treasury = 'TREASURY' in t or 'GOVERNMENT' in t
    
    if scenario == StressScenarioType.MODERATE:
        return 1.5, 0.75
    elif scenario == StressScenarioType.SEVERE:
        return 2.5, 0.40
    elif scenario == StressScenarioType.CREDIT_MARKET_FREEZE:
        if is_treasury:
            return 1.2, 0.90 # modest deterioration for treasuries
        else:
            return 4.0, 0.10 # severe for credit
    
    return 1.0, 1.0
