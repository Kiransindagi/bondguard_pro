import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

vi.mock('react-plotly.js', () => ({
  default: () => <div>Mocked Plotly Chart</div>
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/BondGuard/i)).toBeInTheDocument();
    // 'Dashboard Overview' might be async loaded depending on the route, 
    // but the app should render the header/sidebar immediately.
  });
});
