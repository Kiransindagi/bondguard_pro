import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LiquidityRisk } from '../pages/LiquidityRisk';
import { apiClient } from '../api/client';

vi.mock('react-plotly.js', () => ({
  default: () => <div data-testid="mock-plotly"></div>
}));

vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

const mockSummary = {
  portfolio_market_value: 1000000,
  weighted_liquidity_score: 85,
  estimated_total_liquidation_cost: 2500,
  estimated_total_liquidation_cost_bps: 2.5,
  weighted_days_to_liquidate: 1.5,
  maximum_days_to_liquidate: 3,
  very_low_liquidity_weight: 0.0,
  liquidation_horizon_distribution: []
};

describe('LiquidityRisk Page', () => {
  it('renders loading state then summary data', async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/summary')) return Promise.resolve({ data: mockSummary });
      if (url.includes('/positions')) return Promise.resolve({ data: [] });
      if (url.includes('/limits')) return Promise.resolve({ data: [] });
      if (url.includes('/liquidity-adjusted-var')) return Promise.resolve({ data: { market_var: 10000, liquidity_cost_adjustment: 2500, liquidity_adjusted_var: 12500, market_risk_model_status: 'RATE_ONLY_MODEL', limitations: 'Limitation msg' } });
      if (url.includes('/concentration')) return Promise.resolve({ data: { breakdown: [] } });
      return Promise.resolve({ data: {} });
    });

    render(<LiquidityRisk />);
    
    await waitFor(() => {
      expect(screen.getByText('Liquidity Risk & Concentration')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('$1,000,000')).toBeInTheDocument(); // Market value
      expect(screen.getByText('85.0')).toBeInTheDocument(); // Score
    });
  });

  it('renders RATE_ONLY_MODEL limitation', async () => {
    render(<LiquidityRisk />);
    await waitFor(() => {
      expect(screen.getByText('Limitation msg')).toBeInTheDocument();
    });
  });
});
