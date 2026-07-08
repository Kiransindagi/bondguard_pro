import { useQuery } from '@tanstack/react-query';
import { fetchPortfolios, fetchPortfolioRiskSummary, fetchPortfolioPositionsRisk } from '../api/client';

export const MarketRisk = () => {
  const { data: portfolios, isLoading: loadingPorts } = useQuery({
    queryKey: ['portfolios'],
    queryFn: fetchPortfolios,
  });

  const portfolioId = portfolios && portfolios.length > 0 ? portfolios[0].id : null;

  const { data: summary, isLoading: loadingSummary, isError: errorSummary } = useQuery({
    queryKey: ['portfolioRiskSummary', portfolioId],
    queryFn: () => fetchPortfolioRiskSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: positions, isLoading: loadingPos, isError: errorPos } = useQuery({
    queryKey: ['portfolioPositionsRisk', portfolioId],
    queryFn: () => fetchPortfolioPositionsRisk(portfolioId!),
    enabled: !!portfolioId,
  });

  if (loadingPorts) return <div style={{ color: '#94a3b8' }}>Loading portfolios...</div>;
  if (!portfolios || portfolios.length === 0) return <div style={{ color: '#94a3b8' }}>No portfolios exist.</div>;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1rem' }}>Market Risk</h1>
      
      {loadingSummary ? (
        <p style={{ color: '#94a3b8' }}>Loading risk summary...</p>
      ) : errorSummary ? (
        <p style={{ color: '#ef4444' }}>Error loading risk summary.</p>
      ) : summary && (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
             <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Valuation Date: {summary.valuation_date}</span>
             {summary.curve_date && <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Curve Date: {summary.curve_date}</span>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Total Market Value</h3>
              <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>${Number(summary.total_market_value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
            </div>
            <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Weighted YTM</h3>
              <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>{(Number(summary.weighted_average_ytm || 0) * 100).toFixed(2)}%</p>
            </div>
            <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Modified Duration</h3>
              <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>
                {Number(summary.weighted_modified_duration || 0).toFixed(2)} yrs
              </p>
            </div>
            <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Convexity</h3>
              <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>{Number(summary.weighted_convexity || 0).toFixed(2)}</p>
            </div>
            <div style={{ padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Total DV01</h3>
              <p style={{ color: '#e2e8f0', fontSize: '1.25rem', margin: 0 }}>${Number(summary.total_dv01 || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
            </div>
          </div>
        </>
      )}

      <h2 style={{ fontSize: '1.5rem', color: '#e2e8f0', marginBottom: '1rem' }}>Position Risk Table</h2>
      
      {loadingPos ? (
        <p style={{ color: '#94a3b8' }}>Loading position risks...</p>
      ) : errorPos ? (
        <p style={{ color: '#ef4444' }}>Error loading position risks.</p>
      ) : positions && positions.length > 0 ? (
        <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '0.75rem' }}>Bond ID</th>
                <th style={{ padding: '0.75rem' }}>Market Value</th>
                <th style={{ padding: '0.75rem' }}>Price</th>
                <th style={{ padding: '0.75rem' }}>YTM</th>
                <th style={{ padding: '0.75rem' }}>Mod Dur</th>
                <th style={{ padding: '0.75rem' }}>Convexity</th>
                <th style={{ padding: '0.75rem' }}>DV01</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos: any) => (
                <tr key={pos.bond_id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '0.75rem' }}>{pos.bond_id}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.market_value).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.clean_price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>{(pos.ytm_decimal * 100).toFixed(2)}%</td>
                  <td style={{ padding: '0.75rem' }}>{Number(pos.modified_duration_years).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>{Number(pos.convexity).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(pos.dv01_currency).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ color: '#94a3b8' }}>No active positions found.</p>
      )}
    </div>
  );
};
