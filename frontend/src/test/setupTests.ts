import '@testing-library/jest-dom';
import { vi } from 'vitest';
import React from 'react';

vi.mock('../auth/PortfolioContext', () => ({
  usePortfolio: vi.fn(() => ({
    selectedPortfolioId: 1,
    selectedPortfolio: { id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' },
    portfolios: [{ id: 1, name: 'Global Core', is_active: true, status: 'ACTIVE' }],
    loading: false,
    selectPortfolio: vi.fn(),
    refetchPortfolios: vi.fn(),
  })),
  PortfolioProvider: ({ children }: any) => React.createElement(React.Fragment, null, children),
}));
