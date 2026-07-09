class ScenarioAttribution:
    @staticmethod
    def calculate_attribution(results: dict) -> dict:
        """
        Calculates attribution of P&L impact from scenario results.
        Currently a passthrough that formats position-level impacts.
        """
        # Basic attribution wrapper for future enhancements
        total_pnl = results.get("pnl_impact", 0.0)
        positions = results.get("positions", [])
        
        # Sort positions by highest negative impact
        sorted_positions = sorted(positions, key=lambda x: x["pnl_impact"])
        
        return {
            "total_pnl": total_pnl,
            "worst_contributors": sorted_positions[:5],
            "best_contributors": sorted_positions[-5:] if len(sorted_positions) >= 5 else [],
            "raw_results": results
        }
