import { useQuery } from '@tanstack/react-query';
import { getYieldCurve } from '../api/client';
import Plot from 'react-plotly.js';

export const YieldCurve = () => {
  const { data: curve, isLoading, isError } = useQuery({
    queryKey: ['yieldCurve'],
    queryFn: getYieldCurve
  });

  if (isLoading) return <div style={{ color: '#94a3b8' }}>Loading Yield Curve...</div>;
  if (isError || !curve) return <div style={{ color: '#ef4444' }}>Error loading yield curve data</div>;
  if (curve.length === 0) return <div style={{ color: '#94a3b8' }}>No yield curve data available.</div>;

  const observationDate = curve[0].observation_date;
  const sortedCurve = [...curve].sort((a, b) => a.tenor_years - b.tenor_years);

  const xData = sortedCurve.map(p => p.tenor_years);
  const yData = sortedCurve.map(p => p.yield_percent);

  const getPoint = (tenor: number) => sortedCurve.find(p => p.tenor_years === tenor)?.yield_percent;
  const y2 = getPoint(2);
  const y5 = getPoint(5);
  const y10 = getPoint(10);
  const y30 = getPoint(30);

  const slope10_2 = y10 !== undefined && y2 !== undefined ? y10 - y2 : null;
  const slope30_5 = y30 !== undefined && y5 !== undefined ? y30 - y5 : null;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e2e8f0' }}>Treasury Yield Curve</h1>
      <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>Observation Date: {observationDate}</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>2Y Yield</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{y2 !== undefined ? y2.toFixed(3) + '%' : 'N/A'}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>5Y Yield</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{y5 !== undefined ? y5.toFixed(3) + '%' : 'N/A'}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>10Y Yield</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{y10 !== undefined ? y10.toFixed(3) + '%' : 'N/A'}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>30Y Yield</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{y30 !== undefined ? y30.toFixed(3) + '%' : 'N/A'}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', flex: 1 }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Curve Slopes</h3>
          <div style={{ display: 'flex', gap: '2rem' }}>
            <div>
              <div style={{ color: '#94a3b8' }}>10Y - 2Y</div>
              <div style={{ fontSize: '1.25rem', color: slope10_2 !== null && slope10_2 >= 0 ? '#22c55e' : '#ef4444' }}>
                {slope10_2 !== null ? (slope10_2 * 100).toFixed(1) + ' bps' : 'N/A'}
              </div>
            </div>
            <div>
              <div style={{ color: '#94a3b8' }}>30Y - 5Y</div>
              <div style={{ fontSize: '1.25rem', color: slope30_5 !== null && slope30_5 >= 0 ? '#22c55e' : '#ef4444' }}>
                {slope30_5 !== null ? (slope30_5 * 100).toFixed(1) + ' bps' : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <Plot
          data={[
            {
              x: xData,
              y: yData,
              type: 'scatter',
              mode: 'lines+markers',
              marker: { color: '#38bdf8' },
              line: { shape: 'spline' }
            }
          ]}
          layout={{
            title: 'Par Yield Curve',
            xaxis: { title: 'Tenor (Years)', gridcolor: '#334155', zerolinecolor: '#334155' },
            yaxis: { title: 'Yield (%)', gridcolor: '#334155', zerolinecolor: '#334155' },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e2e8f0' },
            margin: { t: 40, r: 20, l: 40, b: 40 },
            height: 400
          }}
          style={{ width: '100%' }}
          config={{ displayModeBar: false }}
        />
      </div>

      <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '0.75rem' }}>Tenor (Years)</th>
              <th style={{ padding: '0.75rem' }}>Yield (%)</th>
            </tr>
          </thead>
          <tbody>
            {sortedCurve.map(p => (
              <tr key={p.tenor_years} style={{ borderBottom: '1px solid #334155' }}>
                <td style={{ padding: '0.75rem' }}>{p.tenor_years}Y</td>
                <td style={{ padding: '0.75rem' }}>{p.yield_percent.toFixed(4)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
