import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import * as client from '../api/client';
import React from 'react';
import { Overview } from '../pages/Overview';

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

describe('Overview Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('Overview - successful rendering', async () => {
    vi.mocked(client.fetchPortfolioSummary).mockResolvedValue({ total_market_value: 1000000, total_pnl: 50000, total_positions: 10 });
    vi.mocked(client.fetchPortfolioRiskSummary).mockResolvedValue({ weighted_modified_duration: 5.5, total_dv01: -1000 });
    vi.mocked(client.getPortfolioRiskReport).mockResolvedValue({
      report_metadata: { overall_status: 'PASS' },
      market_risk: { historical_var: 10000, expected_shortfall: 15000 },
      limit_summary: { breach_count: 0, warning_count: 0 },
      breach_summary: { open_count: 0, acknowledged_count: 0, resolved_count: 0 },
      liquidity_risk: { liquidity_score: 85, liquidation_cost: 500, weighted_days_to_liquidate: 2.5 },
      concentration: { largest_issuer: 'US Treasury', largest_issuer_weight: 0.12 },
      model_governance: { degraded_models: [], proxy_models: [] }
    } as any);

    renderWithProviders(<Overview />);

    expect(await screen.findByText('Dashboard Overview')).toBeInTheDocument();
    expect(await screen.findByText('$1,000,000.00')).toBeInTheDocument();
    expect(await screen.findByText('5.50 yrs')).toBeInTheDocument();
    expect(await screen.findByText('PASS')).toBeInTheDocument();
  });

  it('Overview - partial API failure', async () => {
    vi.mocked(client.fetchPortfolioSummary).mockResolvedValue({ total_market_value: 1000000, total_pnl: 50000, total_positions: 10 });
    vi.mocked(client.fetchPortfolioRiskSummary).mockRejectedValue(new Error('API Failure'));
    vi.mocked(client.getPortfolioRiskReport).mockResolvedValue(null as any);

    renderWithProviders(<Overview />);

    expect(await screen.findByText('$1,000,000.00')).toBeInTheDocument();
    const unavailableElements = await screen.findAllByText('Data unavailable');
    expect(unavailableElements.length).toBeGreaterThan(0);
  });
});
