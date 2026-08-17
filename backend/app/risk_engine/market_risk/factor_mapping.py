from app.db.models import Bond


class FactorMappingService:
    @staticmethod
    def get_rate_factor_for_tenor(tenor: float) -> str:
        if tenor <= 2.0:
            return "RATE_2.0Y"
        elif tenor <= 5.0:
            return "RATE_5.0Y"
        elif tenor <= 10.0:
            return "RATE_10.0Y"
        else:
            return "RATE_30.0Y"
            
    @staticmethod
    def get_spread_factor_for_bond(bond: Bond) -> str | None:
        if bond.bond_type == "Corporate":
            if bond.bond_name and "Petrobras" in bond.bond_name or bond.credit_rating in ["BB+", "BB-", "B", "CCC"]:
                return "SPREAD_BAMLH0A0HYM2" # Temporary proxy
            else:
                return "SPREAD_BAMLC0A0CM"
        return None
