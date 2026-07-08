import { useQuery } from '@tanstack/react-query';
import { getSpreads, fetchPortfolioPositions } from '../api/client';
import Plot from 'react-plotly.js';

export const CreditRisk = () => {
  const { data: igSpreads, isLoading: isIgLoading } = useQuery({
    queryKey: ['spreads', 'BAMLC0A0CM'],
    queryFn: () => getSpreads('BAMLC0A0CM')
  });

  const { data: hySpreads, isLoading: isHyLoading } = useQuery({
    queryKey: ['spreads', 'BAMLH0A0HYM2'],
    queryFn: () => getSpreads('BAMLH0A0HYM2')
  });
  
  const { data: positions, isLoading: isPosLoading } = useQuery({
    queryKey: ['portfolioPositions', 1],
    queryFn: () => fetchPortfolioPositions(1)
  });

  if (isIgLoading || isHyLoading || isPosLoading) return <div style={{ color: '#94a3b8' }}>Loading Credit Risk...</div>;

  const hasIg = igSpreads && igSpreads.length > 0;
  const hasHy = hySpreads && hySpreads.length > 0;
  
  const latestIg = hasIg ? igSpreads[0] : null;
  const latestHy = hasHy ? hySpreads[0] : null;

  // Chart data
  const igTrace = hasIg ? {
    x: igSpreads.map((s: any) => s.observation_date),
    y: igSpreads.map((s: any) => s.spread_bps),
    type: 'scatter', mode: 'lines', name: 'US Corp IG (OAS)', line: { color: '#38bdf8' }
  } : null;

  const hyTrace = hasHy ? {
    x: hySpreads.map((s: any) => s.observation_date),
    y: hySpreads.map((s: any) => s.spread_bps),
    type: 'scatter', mode: 'lines', name: 'US High Yield (OAS)', line: { color: '#ef4444' }
  } : null;

  const chartData = [igTrace, hyTrace].filter(t => t !== null) as any[];

  // Portfolio distribution
  let sectorDist: Record<string, number> = {};
  let ratingDist: Record<string, number> = {};
  let totalPosValue = 0;

  if (positions) {
    positions.forEach((p: any) => {
      const val = Number(p.market_value) || 0;
      totalPosValue += val;
      const sec = p.bond.sector || 'Unknown';
      const rat = p.bond.credit_rating || 'NR';
      sectorDist[sec] = (sectorDist[sec] || 0) + val;
      ratingDist[rat] = (ratingDist[rat] || 0) + val;
    });
  }

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e2e8f0' }}>Credit Risk & Spreads</h1>
      <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>FRED Market Spreads & Portfolio Exposure</p>
      
      <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155', marginBottom: '2rem' }}>
        <p style={{ margin: 0, color: '#eab308' }}>
          <strong>Note:</strong> FRED spread data represents observed market indices. Bond ratings and sector exposures below reflect synthetic demonstration metadata and market risk model proxy mappings.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>US Corporate IG OAS (BAMLC0A0CM)</h3>
          {latestIg ? (
            <>
              <div style={{ fontSize: '2rem', color: '#e2e8f0' }}>{latestIg.spread_bps.toFixed(0)} bps</div>
              <div style={{ color: '#64748b' }}>As of {latestIg.observation_date}</div>
            </>
          ) : <div style={{ color: '#ef4444' }}>Missing spread history</div>}
        </div>
        
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>US High Yield OAS (BAMLH0A0HYM2)</h3>
          {latestHy ? (
            <>
              <div style={{ fontSize: '2rem', color: '#e2e8f0' }}>{latestHy.spread_bps.toFixed(0)} bps</div>
              <div style={{ color: '#64748b' }}>As of {latestHy.observation_date}</div>
            </>
          ) : <div style={{ color: '#ef4444' }}>Missing spread history</div>}
        </div>
      </div>

      {chartData.length > 0 && (
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
          <Plot
            data={chartData}
            layout={{
              title: 'Historical Credit Spreads (bps)',
              xaxis: { title: 'Date', gridcolor: '#334155', zerolinecolor: '#334155' },
              yaxis: { title: 'Spread (bps)', gridcolor: '#334155', zerolinecolor: '#334155' },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#e2e8f0' },
              margin: { t: 40, r: 20, l: 40, b: 40 },
              height: 350
            }}
            style={{ width: '100%' }}
            config={{ displayModeBar: false }}
          />
        </div>
      )}
      
      <h2 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Portfolio Exposure</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Sector Distribution</h3>
          {Object.entries(sectorDist).map(([sec, val]) => (
            <div key={sec} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8' }}>{sec}</span>
              <span style={{ color: '#e2e8f0' }}>{(val / totalPosValue * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
        
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Rating Distribution</h3>
          {Object.entries(ratingDist).map(([rat, val]) => (
            <div key={rat} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8' }}>{rat}</span>
              <span style={{ color: '#e2e8f0' }}>{(val / totalPosValue * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
