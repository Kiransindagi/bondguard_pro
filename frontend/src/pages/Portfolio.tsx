import { useQuery } from '@tanstack/react-query';
import { fetchPortfolios, fetchPortfolioSummary, fetchPortfolioPositions } from '../api/client';

export const Portfolio = () => {
  const { data: portfolios, isLoading: loadingPorts } = useQuery({
    queryKey: ['portfolios'],
    queryFn: fetchPortfolios,
  });

  const portfolioId = portfolios && portfolios.length > 0 ? portfolios[0].id : null;

  const { data: summary, isLoading: loadingSummary, isError: errorSummary } = useQuery({
    queryKey: ['portfolioSummary', portfolioId],
    queryFn: () => fetchPortfolioSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: positions, isLoading: loadingPos, isError: errorPos } = useQuery({
    queryKey: ['portfolioPositions', portfolioId],
    queryFn: () => fetchPortfolioPositions(portfolioId!),
    enabled: !!portfolioId,
  });

  if (loadingPorts) return <div style={{ color: '#94a3b8' }}>Loading portfolios...</div>;
  if (!portfolios || portfolios.length === 0) return <div style={{ color: '#94a3b8' }}>No portfolios exist.</div>;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1rem' }}>Portfolio Overview</h1>
      
      {loadingSummary ? (
        <p style={{ color: '#94a3b8' }}>Loading summary...</p>
      ) : errorSummary ? (
        <p style={{ color: '#ef4444' }}>Error loading portfolio summary.</p>
      ) : summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
            <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Portfolio Name</h3>
            <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>{summary.name}</p>
          </div>
          <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
            <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Total Market Value</h3>
            <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>${summary.total_market_value?.toLocaleString()}</p>
          </div>
          <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
            <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Unrealized P&L</h3>
            <p style={{ color: summary.total_unrealized_pnl >= 0 ? '#22c55e' : '#ef4444', fontSize: '1.25rem', margin: 0 }}>
              ${summary.total_unrealized_pnl?.toLocaleString()}
            </p>
          </div>
          <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
            <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Positions</h3>
            <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>{summary.position_count}</p>
          </div>
        </div>
      )}

      <h2 style={{ fontSize: '1.5rem', color: '#e2e8f0', marginBottom: '1rem' }}>Positions Table</h2>
      
      {loadingPos ? (
        <p style={{ color: '#94a3b8' }}>Loading positions...</p>
      ) : errorPos ? (
        <p style={{ color: '#ef4444' }}>Error loading positions.</p>
      ) : positions && positions.length > 0 ? (
        <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '0.75rem' }}>Bond</th>
                <th style={{ padding: '0.75rem' }}>Issuer</th>
                <th style={{ padding: '0.75rem' }}>Rating</th>
                <th style={{ padding: '0.75rem' }}>Maturity</th>
                <th style={{ padding: '0.75rem' }}>Coupon</th>
                <th style={{ padding: '0.75rem' }}>Quantity</th>
                <th style={{ padding: '0.75rem' }}>Avg Cost</th>
                <th style={{ padding: '0.75rem' }}>Price</th>
                <th style={{ padding: '0.75rem' }}>Market Value</th>
                <th style={{ padding: '0.75rem' }}>Unrealized P&L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos: any) => (
                <tr key={pos.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '0.75rem' }}>{pos.bond.ticker || pos.bond.isin}</td>
                  <td style={{ padding: '0.75rem' }}>{pos.bond.issuer_name}</td>
                  <td style={{ padding: '0.75rem' }}>{pos.bond.credit_rating || 'NR'}</td>
                  <td style={{ padding: '0.75rem' }}>{pos.bond.maturity_date}</td>
                  <td style={{ padding: '0.75rem' }}>{(pos.bond.coupon_rate * 100).toFixed(2)}%</td>
                  <td style={{ padding: '0.75rem' }}>{pos.quantity}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.average_cost).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.current_clean_price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.market_value).toLocaleString()}</td>
                  <td style={{ padding: '0.75rem', color: pos.unrealized_pnl >= 0 ? '#22c55e' : '#ef4444' }}>
                    ${Number(pos.unrealized_pnl).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ color: '#94a3b8' }}>No positions held.</p>
      )}
    </div>
  );
};
