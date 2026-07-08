import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MarketRisk } from './MarketRisk';
import * as client from '../api/client';

vi.mock('../api/client', () => ({
  fetchPortfolios: vi.fn(),
  fetchPortfolioRiskSummary: vi.fn(),
  fetchPortfolioPositionsRisk: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithClient = (ui: React.ReactElement) => {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe('MarketRisk', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    (client.fetchPortfolios as any).mockImplementation(() => new Promise(() => {}));
    renderWithClient(<MarketRisk />);
    expect(screen.getByText('Loading portfolios...')).toBeInTheDocument();
  });

  it('renders risk summary and positions', async () => {
    (client.fetchPortfolios as any).mockResolvedValue([{ id: 1 }]);
    (client.fetchPortfolioRiskSummary as any).mockResolvedValue({
      valuation_date: '2024-01-01',
      total_market_value: 1000000,
      weighted_average_ytm: 0.05,
      weighted_modified_duration: 4.5,
      weighted_convexity: 25.0,
      total_dv01: 500,
      curve_date: '2024-01-01'
    });
    (client.fetchPortfolioPositionsRisk as any).mockResolvedValue([{
      bond_id: 1,
      market_value: 1000000,
      clean_price: 100,
      ytm_decimal: 0.05,
      modified_duration_years: 4.5,
      convexity: 25.0,
      dv01_currency: 500
    }]);

    renderWithClient(<MarketRisk />);
    
    await waitFor(() => {
      expect(screen.getByText('Valuation Date: 2024-01-01')).toBeInTheDocument();
    });
    
    expect(screen.getAllByText('$1,000,000')[0]).toBeInTheDocument();
    expect(screen.getAllByText('5.00%')[0]).toBeInTheDocument();
    expect(screen.getByText('4.50 yrs')).toBeInTheDocument();
    expect(screen.getAllByText('25.00')[0]).toBeInTheDocument();
    expect(screen.getAllByText('$500')[0]).toBeInTheDocument();
  });

  it('handles API error state gracefully', async () => {
    (client.fetchPortfolios as any).mockResolvedValue([{ id: 1 }]);
    (client.fetchPortfolioRiskSummary as any).mockRejectedValue(new Error('API Error'));
    (client.fetchPortfolioPositionsRisk as any).mockRejectedValue(new Error('API Error'));

    renderWithClient(<MarketRisk />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading risk summary.')).toBeInTheDocument();
      expect(screen.getByText('Error loading position risks.')).toBeInTheDocument();
    });
  });
});
