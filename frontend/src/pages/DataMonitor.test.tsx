import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DataMonitor } from './DataMonitor';
import * as client from '../api/client';

vi.mock('../api/client', () => ({
  fetchDataStatus: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithClient = (ui: React.ReactElement) => {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe('DataMonitor', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    (client.fetchDataStatus as any).mockImplementation(() => new Promise(() => {}));
    renderWithClient(<DataMonitor />);
    expect(screen.getByText('Loading data status...')).toBeInTheDocument();
  });

  it('shows empty state when no data', async () => {
    (client.fetchDataStatus as any).mockResolvedValue([]);
    renderWithClient(<DataMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('No data ingestions have been run yet.')).toBeInTheDocument();
    });
  });

  it('shows error state when API fails', async () => {
    (client.fetchDataStatus as any).mockRejectedValue(new Error('Network Error'));
    renderWithClient(<DataMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading data status')).toBeInTheDocument();
    });
  });

  it('renders successful status response and handles refresh', async () => {
    const mockData = [
      {
        source: 'yfinance',
        dataset: 'ETF_Market_Data',
        last_successful_update: '2023-10-10T10:00:00Z',
        last_status: 'SUCCESS',
        records_fetched: 100,
        records_inserted: 100,
      }
    ];
    (client.fetchDataStatus as any).mockResolvedValue(mockData);
    
    renderWithClient(<DataMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText('ETF_Market_Data')).toBeInTheDocument();
    });
    
    expect(screen.getByText('yfinance')).toBeInTheDocument();
    expect(screen.getByText('SUCCESS')).toBeInTheDocument();
    
    const refreshBtn = screen.getByText('Refresh Data');
    fireEvent.click(refreshBtn);
    
    expect(client.fetchDataStatus).toHaveBeenCalledTimes(2);
  });
});
