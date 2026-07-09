class ScenarioBuilder:
    @staticmethod
    def build_shock_dict(scenario) -> dict:
        """
        Builds a normalized shock dictionary from a SavedScenario model.
        """
        return {
            "rate_2y_shock_bps": getattr(scenario, "rate_2y_shock_bps", 0),
            "rate_5y_shock_bps": getattr(scenario, "rate_5y_shock_bps", 0),
            "rate_10y_shock_bps": getattr(scenario, "rate_10y_shock_bps", 0),
            "rate_30y_shock_bps": getattr(scenario, "rate_30y_shock_bps", 0),
            "ig_spread_shock_bps": getattr(scenario, "ig_spread_shock_bps", 0),
            "hy_spread_shock_bps": getattr(scenario, "hy_spread_shock_bps", 0),
        }
