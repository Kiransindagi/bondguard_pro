import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import * as client from '../api/client';
import React from 'react';
import { CreditRisk } from '../pages/CreditRisk';

vi.mock('../api/client', () => ({
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioRiskSummary: vi.fn(),
  getPortfolioRiskReport: vi.fn(),
  getYieldCurve: vi.fn(),
  getSpreads: vi.fn(),
  fetchPortfolioPositions: vi.fn(),
  fetchPortfolioPositionsRisk: vi.fn(),
}));

vi.mock('react-plotly.js', () => ({
  default: () => <div>Mocked Plotly Chart</div>
}));

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CreditRisk Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('Credit Risk - rendering', async () => {
    vi.mocked(client.getSpreads).mockImplementation((type) => {
      if (type === 'BAMLC0A0CM') return Promise.resolve([{ observation_date: '2025-01-01', spread_bps: 120 }]);
      if (type === 'BAMLH0A0HYM2') return Promise.resolve([{ observation_date: '2025-01-01', spread_bps: 450 }]);
      return Promise.resolve([]);
    });
    vi.mocked(client.fetchPortfolioPositions).mockResolvedValue([]);

    renderWithProviders(<CreditRisk />);

    expect(await screen.findByText('120 bps')).toBeInTheDocument();
    expect(await screen.findByText('450 bps')).toBeInTheDocument();
  });

  it('Credit Risk - missing spread history state', async () => {
    vi.mocked(client.getSpreads).mockResolvedValue([]);
    vi.mocked(client.fetchPortfolioPositions).mockResolvedValue([]);

    renderWithProviders(<CreditRisk />);

    const missingTexts = await screen.findAllByText('Missing spread history');
    expect(missingTexts).toHaveLength(2);
  });
});
