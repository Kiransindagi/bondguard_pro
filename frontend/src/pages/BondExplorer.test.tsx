import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BondExplorer } from './BondExplorer';
import * as client from '../api/client';

vi.mock('../api/client', () => ({
  fetchBonds: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithClient = (ui: React.ReactElement) => {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe('BondExplorer', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('shows loading state', () => {
    (client.fetchBonds as any).mockImplementation(() => new Promise(() => {}));
    renderWithClient(<BondExplorer />);
    expect(screen.getByText('Loading bonds...')).toBeInTheDocument();
  });

  it('renders bonds correctly', async () => {
    (client.fetchBonds as any).mockResolvedValue([{
      id: 1, isin: 'US123', ticker: 'TSLA', issuer_name: 'Tesla', coupon_rate: 0.05, maturity_date: '2025-01-01', sector: 'Consumer'
    }]);

    renderWithClient(<BondExplorer />);
    
    await waitFor(() => {
      expect(screen.getByText('TSLA')).toBeInTheDocument();
    });
    expect(screen.getByText('US123')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    (client.fetchBonds as any).mockRejectedValue(new Error('Network Error'));
    renderWithClient(<BondExplorer />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading bonds.')).toBeInTheDocument();
    });
  });
});
