import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Portfolio } from './Portfolio';
import * as client from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';

vi.mock('../api/client', () => ({
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioPositions: vi.fn(),
}));

vi.mock('../auth/PortfolioContext', () => ({
  usePortfolio: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithClient = (ui: React.ReactElement) => {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe('Portfolio', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('shows empty state when no portfolio selected', () => {
    (usePortfolio as any).mockReturnValue({
      selectedPortfolioId: null,
      selectedPortfolio: null,
      portfolios: null,
      loading: false,
    });

    renderWithClient(<Portfolio />);
    expect(screen.getByText('No portfolio selected.')).toBeInTheDocument();
  });

  it('renders portfolio summary and positions', async () => {
    (usePortfolio as any).mockReturnValue({
      selectedPortfolioId: 1,
      selectedPortfolio: { id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' },
      portfolios: [{ id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' }],
      loading: false,
    });

    (client.fetchPortfolioSummary as any).mockResolvedValue({
      name: 'Global Core',
      total_market_value: 10000,
      total_unrealized_pnl: 500,
      position_count: 1
    });
    (client.fetchPortfolioPositions as any).mockResolvedValue([{
      id: 1,
      quantity: 100,
      average_cost: 95,
      current_clean_price: 100,
      market_value: 10000,
      unrealized_pnl: 500,
      bond: { ticker: 'AAPL', issuer_name: 'Apple', coupon_rate: 0.05, maturity_date: '2030-01-01' }
    }]);

    renderWithClient(<Portfolio />);
    
    await waitFor(() => {
      expect(screen.getByText('Global Core')).toBeInTheDocument();
    });
    
    expect(screen.getAllByText('$10,000')[0]).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('handles API error state gracefully', async () => {
    (usePortfolio as any).mockReturnValue({
      selectedPortfolioId: 1,
      selectedPortfolio: { id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' },
      portfolios: [{ id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' }],
      loading: false,
    });

    (client.fetchPortfolioSummary as any).mockRejectedValue(new Error('API Error'));
    (client.fetchPortfolioPositions as any).mockRejectedValue(new Error('API Error'));

    renderWithClient(<Portfolio />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading portfolio summary.')).toBeInTheDocument();
      expect(screen.getByText('Error loading positions.')).toBeInTheDocument();
    });
  });
});
