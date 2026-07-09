import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import * as client from '../api/client';
import React from 'react';
import { YieldCurve } from '../pages/YieldCurve';

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

describe('YieldCurve Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('Yield Curve - rendering', async () => {
    vi.mocked(client.getYieldCurve).mockResolvedValue([
      { observation_date: '2025-01-01', tenor_years: 2, yield_percent: 4.5 },
      { observation_date: '2025-01-01', tenor_years: 10, yield_percent: 4.0 },
    ]);

    renderWithProviders(<YieldCurve />);

    expect(await screen.findByText('4.500%')).toBeInTheDocument();
    expect(await screen.findByText('4.000%')).toBeInTheDocument();
    expect(await screen.findByText('-50.0 bps')).toBeInTheDocument();
  });

  it('Yield Curve - empty state', async () => {
    vi.mocked(client.getYieldCurve).mockResolvedValue([]);

    renderWithProviders(<YieldCurve />);

    expect(await screen.findByText('No yield curve data available.')).toBeInTheDocument();
  });
});
