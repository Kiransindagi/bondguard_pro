import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import * as client from '../api/client';
import React from 'react';
import { RiskIntelligence } from '../pages/RiskIntelligence';

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

describe('RiskIntelligence Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
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
