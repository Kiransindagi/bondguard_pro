import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { Overview } from '../pages/Overview';
import { YieldCurve } from '../pages/YieldCurve';
import { CreditRisk } from '../pages/CreditRisk';
import { RiskIntelligence } from '../pages/RiskIntelligence';
import * as client from '../api/client';
import React from 'react';

// Mock the API client functions
vi.mock('../api/client', () => ({
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioRiskSummary: vi.fn(),
  getPortfolioRiskReport: vi.fn(),
  getYieldCurve: vi.fn(),
  getSpreads: vi.fn(),
  fetchPortfolioPositions: vi.fn(),
  fetchPortfolioPositionsRisk: vi.fn(),
}));

// Mock react-plotly.js
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

describe('Frontend Coverage Restoration Pass', () => {
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
      liquidity_risk: { liquidity_score: 85, liquidation_cost: 500, weighted_days_to_liquidate: 2.5 },
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
    // Simulate risk summary failure (e.g. returns null/throws error implicitly if mock is empty, or we return null)
    vi.mocked(client.fetchPortfolioRiskSummary).mockRejectedValue(new Error('API Failure'));
    vi.mocked(client.getPortfolioRiskReport).mockResolvedValue(null as any);

    renderWithProviders(<Overview />);

    expect(await screen.findByText('$1,000,000.00')).toBeInTheDocument();
    const unavailableElements = await screen.findAllByText('Data unavailable');
    expect(unavailableElements.length).toBeGreaterThan(0);
  });

  it('Yield Curve - rendering', async () => {
    vi.mocked(client.getYieldCurve).mockResolvedValue([
      { observation_date: '2025-01-01', tenor_years: 2, yield_percent: 4.5 },
      { observation_date: '2025-01-01', tenor_years: 10, yield_percent: 4.0 },
    ]);

    renderWithProviders(<YieldCurve />);

    expect(await screen.findByText('4.500%')).toBeInTheDocument();
    expect(await screen.findByText('4.000%')).toBeInTheDocument();
    expect(await screen.findByText('-50.0 bps')).toBeInTheDocument(); // 10Y - 2Y slope
  });

  it('Yield Curve - empty state', async () => {
    vi.mocked(client.getYieldCurve).mockResolvedValue([]);

    renderWithProviders(<YieldCurve />);

    expect(await screen.findByText('No yield curve data available.')).toBeInTheDocument();
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

  it('Risk Intelligence - degraded RATE_ONLY_MODEL warning', async () => {
    vi.mocked(client.getPortfolioRiskReport).mockResolvedValue({
      model_governance: { degraded_models: ['MARKET_RISK_RATE_ONLY'], proxy_models: [] },
    } as any);
    vi.mocked(client.fetchPortfolioPositionsRisk).mockResolvedValue([]);

    renderWithProviders(<RiskIntelligence />);

    expect(await screen.findByText('Degraded Model: RATE_ONLY_MODEL')).toBeInTheDocument();
  });
});
