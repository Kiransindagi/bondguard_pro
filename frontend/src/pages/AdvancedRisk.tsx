import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPortfolioKeyRateDuration, getPortfolioBucketedDV01, getPortfolioSpreadRisk, getPortfolioCarryRollDown, getPortfolioPnLExplain } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import Plot from 'react-plotly.js';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, EmptyState } from '../components/ui';
import { plotLayout, PLOT_CONFIG, CHART_COLORS } from '../lib/plotlyTheme';

const selectStyle: React.CSSProperties = {
  padding: '7px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '11px',
};

const ShockSlider = ({ label, value, onChange, unit = 'bps', min = -100, max = 100, step = 1 }: any) => (
  <div style={{ marginBottom: '12px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-accent)', fontVariantNumeric: 'tabular-nums' }}>
        {value > 0 ? `+${value}` : value} {unit}
      </span>
    </div>
    <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(Number(e.target.value))} style={{ width: '100%', accentColor: 'var(--accent)' }} />
  </div>
);

export const AdvancedRisk = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();
  const [horizonMonths, setHorizonMonths] = useState(3);
  const [rateShock, setRateShock] = useState(25);
  const [spreadShock, setSpreadShock] = useState(50);
  const [actualPnL, setActualPnL] = useState(-15000);

  const { data: krdData, isLoading: loadingKrd } = useQuery({ queryKey: ['portfolioKrd', portfolioId], queryFn: () => getPortfolioKeyRateDuration(portfolioId!), enabled: !!portfolioId });
  const { data: dv01Data, isLoading: loadingDv01 } = useQuery({ queryKey: ['portfolioBucketedDv01', portfolioId], queryFn: () => getPortfolioBucketedDV01(portfolioId!), enabled: !!portfolioId });
  const { data: spreadData, isLoading: loadingSpread } = useQuery({ queryKey: ['portfolioSpreadRisk', portfolioId], queryFn: () => getPortfolioSpreadRisk(portfolioId!), enabled: !!portfolioId });
  const { data: carryData, isLoading: loadingCarry } = useQuery({ queryKey: ['portfolioCarryRollDown', portfolioId, horizonMonths], queryFn: () => getPortfolioCarryRollDown(portfolioId!, undefined, horizonMonths), enabled: !!portfolioId });
  const { data: pnlData, isLoading: loadingPnl } = useQuery({ queryKey: ['portfolioPnLExplain', portfolioId, rateShock, spreadShock, actualPnL], queryFn: () => getPortfolioPnLExplain(portfolioId!, rateShock, spreadShock, actualPnL), enabled: !!portfolioId });

  if (!portfolioId) return <><PageHeader title="Advanced Fixed-Income Analytics" description="Key rate durations, bucketed DV01, carry & roll down, and P&L explain models" /><EmptyState message="No portfolio selected." /></>;
  if (loadingKrd || loadingDv01 || loadingSpread || loadingCarry || loadingPnl) return <LoadingState message="Loading Advanced Fixed-Income Analytics..." />;

  const krdKeys = krdData ? Object.keys(krdData.key_rate_durations) : [];
  const krdVals = krdData ? Object.values(krdData.key_rate_durations) : [];
  const dv01Keys = dv01Data ? Object.keys(dv01Data.bucketed_dv01) : [];
  const dv01Vals = dv01Data ? Object.values(dv01Data.bucketed_dv01) : [];
  const sectorKeys = spreadData ? Object.keys(spreadData.sector_cs01) : [];
  const sectorVals = spreadData ? Object.values(spreadData.sector_cs01) : [];

  const waterfallData = pnlData ? [{
    type: 'waterfall', orientation: 'v',
    measure: ['relative', 'relative', 'relative', 'relative', 'total', 'relative', 'total'],
    x: ['Carry', 'Rate PnL', 'Spread PnL', 'Convexity', 'Explained', 'Residual', 'Actual'],
    textposition: 'outside',
    y: [pnlData.carry, pnlData.rate_pnl, pnlData.spread_pnl, pnlData.convexity_pnl, pnlData.explained_pnl, pnlData.residual, pnlData.actual_pnl],
    connector: { line: { color: 'var(--border-subtle)' } },
    decreasing: { marker: { color: CHART_COLORS.red } },
    increasing: { marker: { color: CHART_COLORS.primary } },
    totals: { marker: { color: CHART_COLORS.accent } },
  }] : [];

  return (
    <div>
      <PageHeader title="Advanced Risk Analytics" description="Key rate duration, tenor-bucketed DV01, credit spread risk, carry, and P&L attribution" />

      {/* KRD & DV01 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
        <DataPanel title="Key Rate Duration (KRD)">
          {krdData && <Plot data={[{ x: krdKeys.map((k: any) => k.replace('KRD_', '')), y: krdVals, type: 'bar', marker: { color: CHART_COLORS.accent } }]}
            layout={plotLayout({ height: 280, xaxis: { ...plotLayout().xaxis, title: { text: 'Tenor', font: { size: 11, color: '#8fa3bf' } } }, yaxis: { ...plotLayout().yaxis, title: { text: 'Duration (Yrs)', font: { size: 11, color: '#8fa3bf' } } } })}
            config={PLOT_CONFIG} style={{ width: '100%' }} />}
        </DataPanel>
        <DataPanel title="Tenor-Bucketed DV01">
          {dv01Data && <Plot data={[{ x: dv01Keys.map((k: any) => k.replace('DV01_', '')), y: dv01Vals, type: 'bar', marker: { color: CHART_COLORS.amber } }]}
            layout={plotLayout({ height: 280, xaxis: { ...plotLayout().xaxis, title: { text: 'Tenor', font: { size: 11, color: '#8fa3bf' } } }, yaxis: { ...plotLayout().yaxis, title: { text: 'DV01 ($/bp)', font: { size: 11, color: '#8fa3bf' } } } })}
            config={PLOT_CONFIG} style={{ width: '100%' }} />}
        </DataPanel>
      </div>

      {/* CS01 & Carry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
        <DataPanel title="Sector CS01 Spread Sensitivities">
          {spreadData && (
            <>
              <Plot data={[{ labels: sectorKeys, values: sectorVals, type: 'pie', marker: { colors: [CHART_COLORS.purple, CHART_COLORS.red, CHART_COLORS.accent, CHART_COLORS.primary, CHART_COLORS.amber] }, textfont: { color: '#fff', size: 10 } }]}
                layout={plotLayout({ height: 240, showlegend: true, legend: { font: { color: '#8fa3bf', size: 10 } } })}
                config={PLOT_CONFIG} style={{ width: '100%' }} />
              <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '11px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Portfolio CS01: <strong>${spreadData.portfolio_cs01}</strong></span>
                <span style={{ color: 'var(--text-info)' }}>IG CS01: <strong>${spreadData.ig_cs01}</strong></span>
                <span style={{ color: 'var(--text-critical)' }}>HY CS01: <strong>${spreadData.hy_cs01}</strong></span>
              </div>
            </>
          )}
        </DataPanel>

        <DataPanel title="Carry & Roll-Down" headerAction={
          <select value={horizonMonths} onChange={e => setHorizonMonths(Number(e.target.value))} style={selectStyle}>
            <option value="1">1 Month</option><option value="3">3 Months</option>
            <option value="6">6 Months</option><option value="12">12 Months</option>
          </select>
        }>
          {carryData && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <MetricCard label="Yield Carry" value={`${carryData.yield_carry.toFixed(2)}%`} accent />
                <MetricCard label="Roll-Down" value={`${carryData.roll_down_return.toFixed(2)}%`} accent />
              </div>
              <div style={{ backgroundColor: 'var(--bg-inset)', padding: '14px', borderRadius: 'var(--radius-sm)', textAlign: 'center', marginBottom: '10px' }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Projected Return ({horizonMonths}m)</div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-accent)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>{carryData.projected_return.toFixed(2)}%</div>
              </div>
              <p style={{ fontSize: '10px', color: 'var(--text-muted)', margin: 0, fontStyle: 'italic' }}>
                Static calculations assuming unchanged curves and spreads.
              </p>
            </>
          )}
        </DataPanel>
      </div>

      {/* P&L Attribution */}
      <SectionHeader title="P&L Attribution Explain" />
      <DataPanel>
        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '20px' }}>
          <div>
            <ShockSlider label="Rate Shock" value={rateShock} onChange={setRateShock} />
            <ShockSlider label="Spread Shock" value={spreadShock} onChange={setSpreadShock} min={-150} max={150} />
            <ShockSlider label="Actual PnL" value={actualPnL} onChange={setActualPnL} unit="$" min={-50000} max={50000} step={1000} />
          </div>
          <div>
            {pnlData && (
              <Plot data={waterfallData as any}
                layout={plotLayout({ height: 320, yaxis: { ...plotLayout().yaxis, title: { text: 'P&L ($)', font: { size: 11, color: '#8fa3bf' } } } })}
                config={PLOT_CONFIG} style={{ width: '100%' }} />
            )}
          </div>
        </div>
      </DataPanel>
    </div>
  );
};
