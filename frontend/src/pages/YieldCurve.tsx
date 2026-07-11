import { useQuery } from '@tanstack/react-query';
import { getYieldCurve } from '../api/client';
import Plot from 'react-plotly.js';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, ErrorState, TablePanel, Th, Td, KVRow } from '../components/ui';
import { plotLayout, PLOT_CONFIG, CHART_COLORS } from '../lib/plotlyTheme';

export const YieldCurve = () => {
  const { data: curve, isLoading, isError } = useQuery({
    queryKey: ['yieldCurve'],
    queryFn: getYieldCurve,
  });

  if (isLoading) return <LoadingState message="Loading Yield Curve..." />;
  if (isError || !curve) return <ErrorState message="Error loading yield curve data." />;
  if (curve.length === 0) return <DataPanel><div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No yield curve data available.</div></DataPanel>;

  const observationDate = curve[0].observation_date;
  const sortedCurve = [...curve].sort((a: any, b: any) => a.tenor_years - b.tenor_years);
  const xData = sortedCurve.map((p: any) => p.tenor_years);
  const yData = sortedCurve.map((p: any) => p.yield_percent);

  const getPoint = (tenor: number) => sortedCurve.find((p: any) => p.tenor_years === tenor)?.yield_percent;
  const y2 = getPoint(2), y5 = getPoint(5), y10 = getPoint(10), y30 = getPoint(30);
  const slope10_2 = y10 !== undefined && y2 !== undefined ? y10 - y2 : null;
  const slope30_5 = y30 !== undefined && y5 !== undefined ? y30 - y5 : null;

  return (
    <div>
      <PageHeader title="Treasury Yield Curve" description="US Treasury par yields from FRED" context={`Observation: ${observationDate}`} />

      {/* Rate cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        {[{ t: '2Y', v: y2 }, { t: '5Y', v: y5 }, { t: '10Y', v: y10 }, { t: '30Y', v: y30 }].map(r => (
          <MetricCard key={r.t} label={`${r.t} Yield`} value={r.v !== undefined ? `${r.v.toFixed(3)}%` : 'N/A'} />
        ))}
      </div>

      {/* Slopes */}
      <DataPanel title="Curve Slopes" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '32px' }}>
          <KVRow label="10Y - 2Y" value={
            slope10_2 !== null
              ? <span style={{ color: slope10_2 >= 0 ? 'var(--text-positive)' : 'var(--text-critical)' }}>{(slope10_2 * 100).toFixed(1)} bps</span>
              : 'N/A'
          } style={{ flex: 1 }} />
          <KVRow label="30Y - 5Y" value={
            slope30_5 !== null
              ? <span style={{ color: slope30_5 >= 0 ? 'var(--text-positive)' : 'var(--text-critical)' }}>{(slope30_5 * 100).toFixed(1)} bps</span>
              : 'N/A'
          } style={{ flex: 1 }} />
        </div>
      </DataPanel>

      {/* Chart */}
      <DataPanel title="Par Yield Curve" style={{ marginBottom: '20px' }}>
        <Plot
          data={[{
            x: xData, y: yData, type: 'scatter', mode: 'lines+markers',
            marker: { color: CHART_COLORS.accent, size: 6 },
            line: { shape: 'spline', color: CHART_COLORS.accent, width: 2 },
          }]}
          layout={plotLayout({
            height: 380,
            xaxis: { ...plotLayout().xaxis, title: { text: 'Tenor (Years)', font: { size: 11, color: '#8fa3bf' } } },
            yaxis: { ...plotLayout().yaxis, title: { text: 'Yield (%)', font: { size: 11, color: '#8fa3bf' } } },
          })}
          style={{ width: '100%' }}
          config={PLOT_CONFIG}
        />
      </DataPanel>

      {/* Table */}
      <SectionHeader title="Curve Data" />
      <DataPanel noPad>
        <TablePanel>
          <thead><tr><Th>Tenor (Years)</Th><Th right>Yield (%)</Th></tr></thead>
          <tbody>
            {sortedCurve.map((p: any) => (
              <tr key={p.tenor_years}><Td>{p.tenor_years}Y</Td><Td right mono>{p.yield_percent.toFixed(4)}%</Td></tr>
            ))}
          </tbody>
        </TablePanel>
      </DataPanel>
    </div>
  );
};
