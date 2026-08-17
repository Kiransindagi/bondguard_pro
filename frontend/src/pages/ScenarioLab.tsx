import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSavedScenarios, createSavedScenario, deleteSavedScenario, runCustomScenario } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, EmptyState, TablePanel, Th, Td, Btn } from '../components/ui';

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
};

const fmtBps = (v: number) => `${v > 0 ? '+' : ''}${v} bps`;
const fmtCcy = (v: number) => `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const ScenarioLab = () => {
  const queryClient = useQueryClient();
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const [name, setName] = useState('');
  const [rate2y, setRate2y] = useState(0);
  const [rate5y, setRate5y] = useState(0);
  const [rate10y, setRate10y] = useState(0);
  const [rate30y, setRate30y] = useState(0);
  const [igSpread, setIgSpread] = useState(0);
  const [hySpread, setHySpread] = useState(0);
  const [activeTab, setActiveTab] = useState<'run' | 'saved'>('run');
  const [runResult, setRunResult] = useState<any>(null);

  const { data: savedScenarios, isLoading: loadingScens } = useQuery({ queryKey: ['savedScenarios'], queryFn: getSavedScenarios });
  const createMutation = useMutation({ mutationFn: createSavedScenario, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['savedScenarios'] }); setName(''); setActiveTab('saved'); } });
  const deleteMutation = useMutation({ mutationFn: deleteSavedScenario, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['savedScenarios'] }) });
  const runMutation = useMutation({ mutationFn: runCustomScenario, onSuccess: (data) => setRunResult(data) });

  const handleRun = () => runMutation.mutate({ portfolio_id: portfolioId, rate_2y_shock_bps: rate2y, rate_5y_shock_bps: rate5y, rate_10y_shock_bps: rate10y, rate_30y_shock_bps: rate30y, ig_spread_shock_bps: igSpread, hy_spread_shock_bps: hySpread });
  const handleSave = () => { if (!name) return; createMutation.mutate({ name, rate_2y_shock_bps: rate2y, rate_5y_shock_bps: rate5y, rate_10y_shock_bps: rate10y, rate_30y_shock_bps: rate30y, ig_spread_shock_bps: igSpread, hy_spread_shock_bps: hySpread, is_public: true }); };
  const loadShocks = (s: any) => { setRate2y(s.rate_2y_shock_bps); setRate5y(s.rate_5y_shock_bps); setRate10y(s.rate_10y_shock_bps); setRate30y(s.rate_30y_shock_bps); setIgSpread(s.ig_spread_shock_bps); setHySpread(s.hy_spread_shock_bps); setActiveTab('run'); };

  const tabStyle = (active: boolean): React.CSSProperties => ({
    padding: '8px 18px', background: 'transparent', border: 'none',
    borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
    color: active ? 'var(--text-primary)' : 'var(--text-muted)',
    cursor: 'pointer', fontWeight: 600, fontSize: '12px', fontFamily: 'var(--font-sans)',
  });

  const ShockSlider = ({ label, value, onChange, color }: { label: string; value: number; onChange: (v: number) => void; color: string }) => (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontSize: '11px', fontWeight: 600, color, fontVariantNumeric: 'tabular-nums' }}>{fmtBps(value)}</span>
      </div>
      <input type="range" min={-300} max={300} value={value} onChange={e => onChange(Number(e.target.value))} style={{ width: '100%', accentColor: color }} />
    </div>
  );

  if (!portfolioId) {
    return (
      <div>
        <PageHeader title="Scenario What-If Lab" description="Custom rate and credit shock revaluation engine" />
        <EmptyState message="No portfolio selected. Please select a portfolio to design custom scenarios." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Scenario What-If Lab" description="Custom rate and credit shock revaluation engine" />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '24px' }}>
        <button style={tabStyle(activeTab === 'run')} onClick={() => setActiveTab('run')}>Configure & Run</button>
        <button style={tabStyle(activeTab === 'saved')} onClick={() => setActiveTab('saved')}>Saved Scenarios ({savedScenarios?.length || 0})</button>
      </div>

      {activeTab === 'run' ? (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
          {/* Controls panel */}
          <DataPanel>
            <SectionHeader title="Treasury Tenor Shocks" />
            <ShockSlider label="2Y Treasury" value={rate2y} onChange={setRate2y} color="var(--text-accent)" />
            <ShockSlider label="5Y Treasury" value={rate5y} onChange={setRate5y} color="var(--text-accent)" />
            <ShockSlider label="10Y Treasury" value={rate10y} onChange={setRate10y} color="var(--text-accent)" />
            <ShockSlider label="30Y Treasury" value={rate30y} onChange={setRate30y} color="var(--text-accent)" />

            <SectionHeader title="Credit Spread Shocks" style={{ marginTop: '20px' }} />
            <ShockSlider label="Investment Grade (IG)" value={igSpread} onChange={setIgSpread} color="var(--text-info)" />
            <ShockSlider label="High Yield (HY)" value={hySpread} onChange={setHySpread} color="var(--text-critical)" />

            <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Btn variant="primary" onClick={handleRun} disabled={runMutation.isPending} style={{ width: '100%', justifyContent: 'center' }}>
                {runMutation.isPending ? 'Calculating...' : 'Run Stress Test'}
              </Btn>
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', marginTop: '4px' }}>
                <input type="text" placeholder="Scenario Name" value={name} onChange={e => setName(e.target.value)} style={{ ...inputStyle, marginBottom: '8px' }} />
                <Btn variant="secondary" onClick={handleSave} disabled={createMutation.isPending || !name} style={{ width: '100%', justifyContent: 'center' }}>Save to Vault</Btn>
              </div>
            </div>
          </DataPanel>

          {/* Results */}
          <div>
            {runResult ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                  <MetricCard label="Base Market Value" value={fmtCcy(runResult.base_market_value)} />
                  <MetricCard label="Stressed Market Value" value={fmtCcy(runResult.stressed_market_value)} />
                  <MetricCard label="Scenario P&L" value={`${runResult.pnl_impact >= 0 ? '+' : ''}${fmtCcy(runResult.pnl_impact)}`} danger={runResult.pnl_impact < 0} accent={runResult.pnl_impact >= 0} />
                </div>
                <DataPanel title="Position Detail Impact" noPad>
                  <TablePanel>
                    <thead><tr><Th>CUSIP</Th><Th right>Qty</Th><Th right>Base Price</Th><Th right>Stressed Price</Th><Th right>Base MV</Th><Th right>Stressed MV</Th><Th right>PnL</Th></tr></thead>
                    <tbody>
                      {runResult.positions.map((p: any) => (
                        <tr key={p.bond_id}>
                          <Td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{p.cusip}</Td>
                          <Td right mono>{p.quantity.toLocaleString()}</Td>
                          <Td right mono>{p.base_clean_price.toFixed(3)}</Td>
                          <Td right mono>{p.stressed_clean_price.toFixed(3)}</Td>
                          <Td right mono>{fmtCcy(p.base_market_value)}</Td>
                          <Td right mono>{fmtCcy(p.stressed_market_value)}</Td>
                          <Td right mono style={{ color: p.pnl_impact >= 0 ? 'var(--text-positive)' : 'var(--text-critical)' }}>{`${p.pnl_impact >= 0 ? '+' : ''}${fmtCcy(p.pnl_impact)}`}</Td>
                        </tr>
                      ))}
                    </tbody>
                  </TablePanel>
                </DataPanel>
              </>
            ) : (
              <DataPanel style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '280px' }}>
                <EmptyState message="Configure shocks and click Run Stress Test to revalue the portfolio." />
              </DataPanel>
            )}
          </div>
        </div>
      ) : (
        /* Saved scenarios list */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {loadingScens ? <LoadingState /> : savedScenarios && savedScenarios.length > 0 ? savedScenarios.map((scen: any) => (
            <DataPanel key={scen.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>{scen.name}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '8px' }}>Creator: User {scen.creator_user_id} | v{scen.version}</div>
                  <div style={{ display: 'flex', gap: '12px', fontSize: '11px', flexWrap: 'wrap' }}>
                    <span style={{ color: 'var(--text-accent)' }}>2Y: {fmtBps(scen.rate_2y_shock_bps)}</span>
                    <span style={{ color: 'var(--text-accent)' }}>5Y: {fmtBps(scen.rate_5y_shock_bps)}</span>
                    <span style={{ color: 'var(--text-accent)' }}>10Y: {fmtBps(scen.rate_10y_shock_bps)}</span>
                    <span style={{ color: 'var(--text-accent)' }}>30Y: {fmtBps(scen.rate_30y_shock_bps)}</span>
                    <span style={{ color: 'var(--text-info)' }}>IG: {fmtBps(scen.ig_spread_shock_bps)}</span>
                    <span style={{ color: 'var(--text-critical)' }}>HY: {fmtBps(scen.hy_spread_shock_bps)}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                  <Btn variant="secondary" size="sm" onClick={() => loadShocks(scen)}>Load</Btn>
                  <Btn variant="danger" size="sm" onClick={() => deleteMutation.mutate(scen.id)}>Delete</Btn>
                </div>
              </div>
            </DataPanel>
          )) : <EmptyState message="No saved scenarios. Create one in the Run tab." />}
        </div>
      )}
    </div>
  );
};
