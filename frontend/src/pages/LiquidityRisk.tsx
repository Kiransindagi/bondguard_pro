import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, ModelStatusBanner, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td, Btn, KVRow, StatusBadge } from '../components/ui';
import { plotLayout, PLOT_CONFIG, CHART_COLORS } from '../lib/plotlyTheme';

const selectStyle: React.CSSProperties = {
  padding: '7px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '11px',
};

export const LiquidityRisk: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [concentration, setConcentration] = useState<any>(null);
  const [limits, setLimits] = useState<any[]>([]);
  const [varData, setVarData] = useState<any>(null);
  const [stressData, setStressData] = useState<any>(null);
  const [dimension, setDimension] = useState('sector');
  const [scenario, setScenario] = useState('NORMAL');
  const [error, setError] = useState<string | null>(null);
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const loadData = async () => {
    if (!portfolioId) return;
    setLoading(true); setError(null);
    try {
      const [sumRes, posRes, limRes, varRes] = await Promise.all([
        apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/summary`),
        apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/positions`),
        apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/limits`),
        apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/liquidity-adjusted-var`),
      ]);
      setSummary(sumRes.data); setPositions(posRes.data); setLimits(limRes.data); setVarData(varRes.data);
      await loadConcentration(dimension);
    } catch (err: any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const loadConcentration = async (dim: string) => {
    if (!portfolioId) return;
    try { setConcentration((await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/concentration?dimension=${dim}`)).data); }
    catch (err) { console.error(err); }
  };

  const runSnapshot = async () => {
    if (!portfolioId) return;
    setLoading(true);
    try { await apiClient.post(`/liquidity-risk/portfolios/${portfolioId}/snapshot`); await loadData(); }
    catch (err: any) { setError(err.response?.data?.detail || err.message); setLoading(false); }
  };

  const runStress = async (sc: string) => {
    if (!portfolioId) return;
    setScenario(sc);
    if (sc === 'NORMAL') { setStressData(null); return; }
    try { setStressData((await apiClient.post(`/liquidity-risk/portfolios/${portfolioId}/stress`, { scenario: sc })).data); }
    catch (err) { console.error(err); }
  };

  useEffect(() => { loadData(); }, [portfolioId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (summary) loadConcentration(dimension); }, [dimension, portfolioId]); // eslint-disable-line react-hooks/exhaustive-deps

  const fmtCcy = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);

  if (!portfolioId) return <><PageHeader title="Liquidity Risk & Concentration" description="Transaction costs, liquidation horizons, and portfolio concentration" /><EmptyState message="No portfolio selected." /></>;

  return (
    <div>
      <PageHeader
        title="Liquidity Risk & Concentration"
        description="Transaction costs, liquidation horizons, and portfolio concentration"
        action={<Btn variant="primary" size="sm" onClick={runSnapshot} disabled={loading}>{loading ? 'Running...' : 'Generate Snapshot'}</Btn>}
      />

      <ModelStatusBanner variant="info" status="CHARACTERISTIC_BASED_PROXY_V1" message="Liquidity metrics use characteristic-based proxy classification. Actual trading conditions may differ." />

      {error && <ErrorState message={error} />}

      {summary && (
        <>
          {/* Core metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(185px, 1fr))', gap: '12px', marginBottom: '24px' }}>
            <MetricCard label="Portfolio Market Value" value={fmtCcy(summary.portfolio_market_value)} />
            <MetricCard label="Liquidity Score" value={summary.weighted_liquidity_score.toFixed(1)} unit="/ 100" accent />
            <MetricCard label="Liquidation Cost" value={fmtCcy(summary.estimated_total_liquidation_cost)} sub={`${summary.estimated_total_liquidation_cost_bps.toFixed(2)} bps`} danger />
            <MetricCard label="Days to Liquidate" value={summary.weighted_days_to_liquidate.toFixed(1)} sub={`Max: ${summary.maximum_days_to_liquidate}`} />
          </div>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
            <DataPanel title="Liquidation Horizon Distribution">
              <Plot
                data={[{ x: summary.liquidation_horizon_distribution.map((d: any) => d.bucket.replace(/_/g, ' ')), y: summary.liquidation_horizon_distribution.map((d: any) => d.market_value), type: 'bar', marker: { color: CHART_COLORS.purple } }]}
                layout={plotLayout({ height: 280, xaxis: { ...plotLayout().xaxis, tickangle: -20 } })}
                config={PLOT_CONFIG} style={{ width: '100%' }}
              />
            </DataPanel>
            <DataPanel title="Concentration Analytics" headerAction={
              <select value={dimension} onChange={e => setDimension(e.target.value)} style={selectStyle}>
                <option value="issuer">Issuer</option><option value="sector">Sector</option>
                <option value="country">Country</option><option value="rating">Rating</option><option value="maturity">Maturity</option>
              </select>
            }>
              {concentration && (
                <Plot
                  data={[{ x: concentration.breakdown.slice(0, 10).map((d: any) => d.name), y: concentration.breakdown.slice(0, 10).map((d: any) => d.market_value), type: 'bar', marker: { color: CHART_COLORS.primary } }]}
                  layout={plotLayout({ height: 280, xaxis: { ...plotLayout().xaxis, tickangle: -20 } })}
                  config={PLOT_CONFIG} style={{ width: '100%' }}
                />
              )}
            </DataPanel>
          </div>

          {/* VaR + Stress row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
            <DataPanel title="Liquidity-Adjusted VaR">
              {varData ? (
                <>
                  <KVRow label="Market VaR" value={fmtCcy(varData.market_var)} />
                  <KVRow label="Liquidity Cost Adjustment" value={<span style={{ color: 'var(--text-critical)' }}>+{fmtCcy(varData.liquidity_cost_adjustment)}</span>} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '12px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>Liquidity-Adjusted VaR</span>
                    <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-critical)', fontVariantNumeric: 'tabular-nums' }}>{fmtCcy(varData.liquidity_adjusted_var)}</span>
                  </div>
                  {varData.market_risk_model_status === 'RATE_ONLY_MODEL' && (
                    <div style={{ marginTop: '12px', padding: '8px 12px', backgroundColor: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--text-warning)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                      {varData.limitations}
                    </div>
                  )}
                </>
              ) : <LoadingState />}
            </DataPanel>

            <DataPanel title="Liquidity Stress Testing" headerAction={
              <select value={scenario} onChange={e => runStress(e.target.value)} style={selectStyle}>
                <option value="NORMAL">Normal</option><option value="MODERATE">Moderate</option>
                <option value="SEVERE">Severe</option><option value="CREDIT_MARKET_FREEZE">Credit Freeze</option>
              </select>
            }>
              {stressData ? (
                <>
                  <KVRow label="Normal Cost" value={fmtCcy(stressData.normal_liquidation_cost)} />
                  <KVRow label="Stressed Cost" value={<span style={{ color: 'var(--text-critical)', fontWeight: 600 }}>{fmtCcy(stressData.stressed_liquidation_cost)}</span>} />
                  <KVRow label="Normal Days" value={`${stressData.normal_days_to_liquidate.toFixed(1)} days`} />
                  <KVRow label="Stressed Days" value={<span style={{ color: 'var(--text-critical)', fontWeight: 600 }}>{stressData.stressed_days_to_liquidate.toFixed(1)} days</span>} />
                </>
              ) : <EmptyState message="Select a stress scenario to view impact." />}
            </DataPanel>
          </div>

          {/* Concentration limits */}
          <SectionHeader title="Concentration Limits" />
          <DataPanel noPad style={{ marginBottom: '24px' }}>
            <TablePanel>
              <thead><tr><Th>Limit Type</Th><Th right>Threshold</Th><Th right>Warning</Th><Th>Status</Th></tr></thead>
              <tbody>
                {limits.length > 0 ? limits.map((lim: any, i: number) => (
                  <tr key={i}>
                    <Td>{lim.limit.limit_type.replace(/_/g, ' ')}</Td>
                    <Td right mono>{(lim.limit.threshold_value * 100).toFixed(1)}%</Td>
                    <Td right mono>{(lim.limit.warning_threshold_value * 100).toFixed(1)}%</Td>
                    <Td><StatusBadge label={lim.status} variant={lim.status === 'OK' ? 'ok' : lim.status === 'WARNING' ? 'warning' : 'danger'} /></Td>
                  </tr>
                )) : <tr><td colSpan={4}><EmptyState message="No limits configured." /></td></tr>}
              </tbody>
            </TablePanel>
          </DataPanel>

          {/* Position details */}
          <SectionHeader title="Position Liquidity Details" />
          <DataPanel noPad>
            <TablePanel>
              <thead><tr><Th>Bond</Th><Th>Class</Th><Th right>Score</Th><Th right>Spread (bps)</Th><Th right>Est. Cost</Th><Th right>Days</Th></tr></thead>
              <tbody>
                {positions.map((pos: any) => (
                  <tr key={pos.position_id}>
                    <Td>{pos.bond_name}</Td>
                    <Td><StatusBadge label={pos.liquidity_class} variant={pos.liquidity_class === 'HIGH' ? 'ok' : pos.liquidity_class === 'MEDIUM' ? 'info' : 'warning'} /></Td>
                    <Td right mono>{pos.liquidity_score.toFixed(1)}</Td>
                    <Td right mono>{pos.estimated_bid_ask_bps.toFixed(1)}</Td>
                    <Td right mono>{fmtCcy(pos.estimated_liquidation_cost)}</Td>
                    <Td right mono>{pos.estimated_trading_days_to_liquidate}</Td>
                  </tr>
                ))}
              </tbody>
            </TablePanel>
          </DataPanel>
        </>
      )}
    </div>
  );
};
