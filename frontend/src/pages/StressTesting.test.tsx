import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StressTesting } from './StressTesting';
import { fetchScenarios, runStressTest, compareScenarios } from '../api/stressTesting';
import { usePortfolio } from '../auth/PortfolioContext';

vi.mock('../api/stressTesting');

vi.mock('../auth/PortfolioContext', () => ({
  usePortfolio: vi.fn(),
}));

const mockScenarios = [
  {
    id: 1,
    name: 'RATE_UP_100BP',
    scenario_type: 'PARALLEL_RATE',
    is_predefined: true,
  },
  {
    id: 2,
    name: 'RATE_DOWN_100BP',
    scenario_type: 'PARALLEL_RATE',
    is_predefined: true,
  }
];

const mockRunResult = {
  id: 1,
  portfolio_id: 1,
  scenario_id: 1,
  valuation_date: '2024-01-01',
  calculation_method: 'FULL_REVALUATION',
  base_market_value: 1000000,
  stressed_market_value: 900000,
  total_pnl: -100000,
  total_loss_percent: -10.0,
  position_count: 1,
  positions: [
    {
      id: 1,
      bond_id: 1,
      bond_name: 'Test Bond',
      rating: 'AAA',
      base_clean_price: 100,
      stressed_clean_price: 90,
      rate_shock_bps: 100,
      spread_shock_bps: 0,
      pnl: -10000,
      contribution_percent: -10,
    }
  ]
};

const mockComparisonResult = {
  portfolio_id: 1,
  valuation_date: '2024-01-01',
  scenarios: [
    {
      scenario_name: 'RATE_UP_100BP',
      total_pnl: -100000,
    },
    {
      scenario_name: 'RATE_DOWN_100BP',
      total_pnl: 100000,
    }
  ]
};

describe('StressTesting Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (fetchScenarios as any).mockResolvedValue(mockScenarios);
    (runStressTest as any).mockResolvedValue(mockRunResult);
    (compareScenarios as any).mockResolvedValue(mockComparisonResult);
  });

  it('shows empty state when no portfolio selected', () => {
    (usePortfolio as any).mockReturnValue({
      selectedPortfolioId: null,
      selectedPortfolio: null,
      portfolios: null,
      loading: false,
    });

    render(<StressTesting />);
    expect(screen.getByText('No portfolio selected. Please select a portfolio to run stress tests.')).toBeInTheDocument();
  });

  it('renders correctly and loads scenarios', async () => {
    (usePortfolio as any).mockReturnValue({
      selectedPortfolioId: 1,
      selectedPortfolio: { id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' },
      portfolios: [{ id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' }],
      loading: false,
    });

    render(<StressTesting />);
    expect(screen.getByText('Stress Testing')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(fetchScenarios).toHaveBeenCalled();
    });
  });
});
