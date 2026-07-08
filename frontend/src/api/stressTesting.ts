import { apiClient } from './client';

export interface StressScenario {
  id: number;
  name: string;
  description: string | null;
  scenario_type: string;
  is_predefined: boolean;
  rate_2y_shock_bps: number;
  rate_5y_shock_bps: number;
  rate_10y_shock_bps: number;
  rate_30y_shock_bps: number;
  ig_spread_shock_bps: number;
  hy_spread_shock_bps: number;
  default_calculation_method: string;
}

export interface StressPositionResult {
  id: number;
  bond_id: number;
  bond_name: string;
  issuer: string;
  rating: string;
  sector: string;
  base_clean_price: number;
  stressed_clean_price: number;
  base_market_value: number;
  stressed_market_value: number;
  rate_shock_bps: number;
  spread_shock_bps: number;
  pnl: number;
  pnl_percent: number;
  contribution_percent: number;
}

export interface StressRunResponse {
  id: number;
  portfolio_id: number;
  scenario_id: number;
  valuation_date: string;
  calculation_method: string;
  base_market_value: number;
  stressed_market_value: number;
  total_pnl: number;
  total_loss_percent: number;
  position_count: number;
  positions: StressPositionResult[];
}

export interface PortfolioStressSummary {
  portfolio_id: number;
  scenario_id: number;
  scenario_name: string;
  valuation_date: string;
  calculation_method: string;
  base_market_value: number;
  stressed_market_value: number;
  total_pnl: number;
  total_loss_percent: number;
  largest_loss_position_bond_id: number | null;
  largest_gain_position_bond_id: number | null;
  position_count: number;
  rate_scenario_description: string;
  credit_scenario_description: string;
  limitations: string | null;
}

export interface StressComparisonResponse {
  portfolio_id: number;
  valuation_date: string;
  scenarios: PortfolioStressSummary[];
}

export const fetchScenarios = async (): Promise<StressScenario[]> => {
  const response = await apiClient.get('/stress-scenarios');
  return response.data;
};

export const runStressTest = async (portfolioId: number, scenarioId: number, calculationMethod?: string): Promise<StressRunResponse> => {
  const payload: any = { scenario_id: scenarioId };
  if (calculationMethod) {
    payload.calculation_method = calculationMethod;
  }
  const response = await apiClient.post(`/stress-tests/portfolios/${portfolioId}/run`, payload);
  return response.data;
};

export const compareScenarios = async (portfolioId: number, scenarioIds: number[]): Promise<StressComparisonResponse> => {
  const response = await apiClient.post(`/stress-tests/portfolios/${portfolioId}/compare`, { scenario_ids: scenarioIds });
  return response.data;
};
