import React, { useState, useEffect } from 'react';
import { fetchScenarios, runStressTest, compareScenarios } from '../api/stressTesting';
import type { StressScenario, StressRunResponse, StressComparisonResponse } from '../api/stressTesting';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, ErrorState, TablePanel, Th, Td, Btn, EmptyState } from '../components/ui';

export const StressTesting: React.FC = () => {
  const [scenarios, setScenarios] = useState<StressScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<StressRunResponse | null>(null);
  const [comparisonResult, setComparisonResult] = useState<StressComparisonResponse | null>(null);
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  useEffect(() => { loadScenarios(); }, []);
  useEffect(() => {
    setRunResult(null);
    setComparisonResult(null);
  }, [portfolioId]);

  const loadScenarios = async () => {
    try { setScenarios(await fetchScenarios()); }
    catch (err: any) { setError(err.message || 'Failed to load scenarios'); }
  };

  const handleRunScenario = async () => {
    if (selectedScenarioId === '') return;
    setLoading(true); setError(null); setComparisonResult(null);
    try { setRunResult(await runStressTest(portfolioId!, selectedScenarioId as number)); }
    catch (err: any) { setError(err.message || 'Failed to run scenario'); }
    finally { setLoading(false); }
  };

  const handleCompareAll = async () => {
    setLoading(true); setError(null); setRunResult(null);
    try {
      const ids = scenarios.filter(s => s.is_predefined).map(s => s.id).slice(0, 5);
      setComparisonResult(await compareScenarios(portfolioId!, ids));
    } catch (err: any) { setError(err.message || 'Failed to compare scenarios'); }
    finally { setLoading(false); }
  };

  const fmtCcy = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);
  const fmtPct = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;

  if (!portfolioId) {
    return (
      <div>
        <PageHeader title="Stress Testing" description="Full-revaluation scenario analysis and portfolio impact" />
        <EmptyState message="No portfolio selected. Please select a portfolio to run stress tests." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Stress Testing" description="Full-revaluation scenario analysis and portfolio impact" />

      {error && <ErrorState message={error} />}

      {/* Controls */}
      <DataPanel style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            value={selectedScenarioId}
            onChange={e => setSelectedScenarioId(Number(e.target.value))}
            style={{
              flex: 1, padding: '9px 14px', borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
              border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
            }}
          >
            <option value="">Select Scenario</option>
            {scenarios.map(s => (
              <option key={s.id} value={s.id}>{s.name} - {s.scenario_type.replace('_', ' ')}</option>
            ))}
          </select>
          <Btn variant="primary" onClick={handleRunScenario} disabled={loading || selectedScenarioId === ''}>Run Scenario</Btn>
          <Btn variant="ghost" onClick={handleCompareAll} disabled={loading}>Compare Top 5</Btn>
        </div>
      </DataPanel>

      {loading && <LoadingState message="Running calculations..." />}

      {/* Single run result */}
      {runResult && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
            <MetricCard label="Total P&L" value={fmtCcy(runResult.total_pnl)} danger={runResult.total_pnl < 0} accent={runResult.total_pnl >= 0} />
            <MetricCard label="Loss %" value={fmtPct(runResult.total_loss_percent)} danger={runResult.total_loss_percent < 0} />
            <MetricCard label="Base Market Value" value={fmtCcy(runResult.base_market_value)} />
            <MetricCard label="Stressed Market Value" value={fmtCcy(runResult.stressed_market_value)} />
          </div>

          <SectionHeader title="Position Attribution" />
          <DataPanel noPad>
            <TablePanel>
              <thead>
                <tr>
                  <Th>Bond</Th><Th>Rating</Th>
                  <Th right>Base Price</Th><Th right>Stressed Price</Th>
                  <Th right>Rate Shock (bps)</Th><Th right>Spread Shock (bps)</Th>
                  <Th right>PnL</Th><Th right>Contrib %</Th>
                </tr>
              </thead>
              <tbody>
                {runResult.positions.map(pos => (
                  <tr key={pos.id}>
                    <Td>{pos.bond_name}</Td>
                    <Td>{pos.rating}</Td>
                    <Td right mono>{pos.base_clean_price.toFixed(2)}</Td>
                    <Td right mono>{pos.stressed_clean_price.toFixed(2)}</Td>
                    <Td right mono>{pos.rate_shock_bps.toFixed(1)}</Td>
                    <Td right mono>{pos.spread_shock_bps.toFixed(1)}</Td>
                    <Td right mono style={{ color: pos.pnl < 0 ? 'var(--text-critical)' : 'var(--text-positive)' }}>{fmtCcy(pos.pnl)}</Td>
                    <Td right mono>{pos.contribution_percent.toFixed(2)}%</Td>
                  </tr>
                ))}
              </tbody>
            </TablePanel>
          </DataPanel>
        </>
      )}

      {/* Comparison */}
      {comparisonResult && (
        <>
          <SectionHeader title="Scenario Comparison" style={{ marginTop: '28px' }} />
          <DataPanel noPad>
            <TablePanel>
              <thead>
                <tr>
                  <Th>Scenario</Th><Th right>Total PnL</Th><Th right>Loss %</Th><Th>Method</Th>
                </tr>
              </thead>
              <tbody>
                {comparisonResult.scenarios.map((scen, idx) => (
                  <tr key={idx}>
                    <Td>{scen.scenario_name}</Td>
                    <Td right mono style={{ color: scen.total_pnl < 0 ? 'var(--text-critical)' : 'var(--text-positive)' }}>{fmtCcy(scen.total_pnl)}</Td>
                    <Td right mono style={{ color: scen.total_loss_percent < 0 ? 'var(--text-critical)' : 'var(--text-positive)' }}>{fmtPct(scen.total_loss_percent)}</Td>
                    <Td>{scen.calculation_method}</Td>
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

export default StressTesting;
