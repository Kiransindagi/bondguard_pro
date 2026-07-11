import { useQuery } from '@tanstack/react-query';
import { getSpreads, fetchPortfolioPositions } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import Plot from 'react-plotly.js';
import { PageHeader, MetricCard, DataPanel, SectionHeader, ModelStatusBanner, LoadingState, KVRow, EmptyState } from '../components/ui';
import { plotLayout, PLOT_CONFIG, CHART_COLORS } from '../lib/plotlyTheme';

export const CreditRisk = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: igSpreads, isLoading: isIgLoading } = useQuery({
    queryKey: ['spreads', 'BAMLC0A0CM'],
    queryFn: () => getSpreads('BAMLC0A0CM'),
  });

  const { data: hySpreads, isLoading: isHyLoading } = useQuery({
    queryKey: ['spreads', 'BAMLH0A0HYM2'],
    queryFn: () => getSpreads('BAMLH0A0HYM2'),
  });

  const { data: positions, isLoading: isPosLoading } = useQuery({
    queryKey: ['portfolioPositions', portfolioId],
    queryFn: () => fetchPortfolioPositions(portfolioId!),
    enabled: !!portfolioId,
  });

  if (!portfolioId) return <><PageHeader title="Credit Risk & Spreads" description="Systemic credit spreads, historical trends, and exposure distribution" /><EmptyState message="No portfolio selected." /></>;
  if (isIgLoading || isHyLoading || isPosLoading) return <LoadingState message="Loading Credit Risk..." />;

  const hasIg = igSpreads && igSpreads.length > 0;
  const hasHy = hySpreads && hySpreads.length > 0;
  const latestIg = hasIg ? igSpreads[0] : null;
  const latestHy = hasHy ? hySpreads[0] : null;

  const igTrace = hasIg ? {
    x: igSpreads.map((s: any) => s.observation_date),
    y: igSpreads.map((s: any) => s.spread_bps),
    type: 'scatter', mode: 'lines', name: 'US Corp IG (OAS)',
    line: { color: CHART_COLORS.accent, width: 2 },
  } : null;

  const hyTrace = hasHy ? {
    x: hySpreads.map((s: any) => s.observation_date),
    y: hySpreads.map((s: any) => s.spread_bps),
    type: 'scatter', mode: 'lines', name: 'US High Yield (OAS)',
    line: { color: CHART_COLORS.red, width: 2 },
  } : null;

  const chartData = [igTrace, hyTrace].filter(t => t !== null) as any[];

  let sectorDist: Record<string, number> = {};
  let ratingDist: Record<string, number> = {};
  let totalPosValue = 0;

  if (positions) {
    positions.forEach((p: any) => {
      const val = Number(p.market_value) || 0;
      totalPosValue += val;
      sectorDist[p.bond.sector || 'Unknown'] = (sectorDist[p.bond.sector || 'Unknown'] || 0) + val;
      ratingDist[p.bond.credit_rating || 'NR'] = (ratingDist[p.bond.credit_rating || 'NR'] || 0) + val;
    });
  }

  return (
    <div>
      <PageHeader title="Credit Risk & Spreads" description="FRED market index spreads and portfolio credit exposure" />

      <ModelStatusBanner
        variant="info"
        status="Data Source"
        message="FRED spread data represents observed market indices. Bond ratings and sector exposures reflect synthetic demonstration metadata and proxy mappings."
      />

      {/* Spread cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
        <MetricCard
          label="US Corporate IG OAS (BAMLC0A0CM)"
          value={latestIg ? `${latestIg.spread_bps.toFixed(0)}` : 'N/A'}
          unit="bps"
          sub={latestIg ? `As of ${latestIg.observation_date}` : 'Missing spread history'}
          danger={!latestIg}
        />
        <MetricCard
          label="US High Yield OAS (BAMLH0A0HYM2)"
          value={latestHy ? `${latestHy.spread_bps.toFixed(0)}` : 'N/A'}
          unit="bps"
          sub={latestHy ? `As of ${latestHy.observation_date}` : 'Missing spread history'}
          danger={!latestHy}
        />
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <DataPanel title="Historical Credit Spreads" style={{ marginBottom: '20px' }}>
          <Plot
            data={chartData}
            layout={plotLayout({
              height: 340,
              yaxis: { ...plotLayout().yaxis, title: { text: 'Spread (bps)', font: { size: 11, color: '#8fa3bf' } } },
            })}
            style={{ width: '100%' }}
            config={PLOT_CONFIG}
          />
        </DataPanel>
      )}

      {/* Portfolio exposure */}
      <SectionHeader title="Portfolio Exposure" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <DataPanel title="Sector Distribution">
          {Object.entries(sectorDist).map(([sec, val]) => (
            <KVRow key={sec} label={sec} value={`${(val / totalPosValue * 100).toFixed(1)}%`} />
          ))}
        </DataPanel>
        <DataPanel title="Rating Distribution">
          {Object.entries(ratingDist).map(([rat, val]) => (
            <KVRow key={rat} label={rat} value={`${(val / totalPosValue * 100).toFixed(1)}%`} />
          ))}
        </DataPanel>
      </div>
    </div>
  );
};
