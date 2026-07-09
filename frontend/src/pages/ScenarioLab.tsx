import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSavedScenarios, createSavedScenario, deleteSavedScenario, runCustomScenario } from '../api/client';

export const ScenarioLab = () => {
  const queryClient = useQueryClient();
  const portfolioId = 1;

  // Form states for shocks
  const [name, setName] = useState('');
  const [rate2y, setRate2y] = useState(0);
  const [rate5y, setRate5y] = useState(0);
  const [rate10y, setRate10y] = useState(0);
  const [rate30y, setRate30y] = useState(0);
  const [igSpread, setIgSpread] = useState(0);
  const [hySpread, setHySpread] = useState(0);

  const [activeTab, setActiveTab] = useState<'run' | 'saved'>('run');
  const [runResult, setRunResult] = useState<any>(null);

  // Queries
  const { data: savedScenarios, isLoading: loadingScens } = useQuery({
    queryKey: ['savedScenarios'],
    queryFn: getSavedScenarios
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createSavedScenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedScenarios'] });
      setName('');
      setActiveTab('saved');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSavedScenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedScenarios'] });
    }
  });

  const runMutation = useMutation({
    mutationFn: runCustomScenario,
    onSuccess: (data) => {
      setRunResult(data);
    }
  });

  const handleRun = () => {
    runMutation.mutate({
      portfolio_id: portfolioId,
      rate_2y_shock_bps: rate2y,
      rate_5y_shock_bps: rate5y,
      rate_10y_shock_bps: rate10y,
      rate_30y_shock_bps: rate30y,
      ig_spread_shock_bps: igSpread,
      hy_spread_shock_bps: hySpread
    });
  };

  const handleSave = () => {
    if (!name) return alert('Please enter a scenario name.');
    createMutation.mutate({
      name,
      rate_2y_shock_bps: rate2y,
      rate_5y_shock_bps: rate5y,
      rate_10y_shock_bps: rate10y,
      rate_30y_shock_bps: rate30y,
      ig_spread_shock_bps: igSpread,
      hy_spread_shock_bps: hySpread,
      is_public: true
    });
  };

  const loadScenarioShocks = (scen: any) => {
    setRate2y(scen.rate_2y_shock_bps);
    setRate5y(scen.rate_5y_shock_bps);
    setRate10y(scen.rate_10y_shock_bps);
    setRate30y(scen.rate_30y_shock_bps);
    setIgSpread(scen.ig_spread_shock_bps);
    setHySpread(scen.hy_spread_shock_bps);
    setActiveTab('run');
  };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1.5rem' }}>Scenario What-If Lab</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '1px solid #334155' }}>
        <button
          onClick={() => setActiveTab('run')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'transparent',
            color: activeTab === 'run' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            borderBottom: activeTab === 'run' ? '2px solid #38bdf8' : 'none',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Configure & Run
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'transparent',
            color: activeTab === 'saved' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            borderBottom: activeTab === 'saved' ? '2px solid #38bdf8' : 'none',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Saved Scenarios ({savedScenarios?.length || 0})
        </button>
      </div>

      {activeTab === 'run' ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
          {/* Controls */}
          <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <h3 style={{ color: '#e2e8f0', marginBottom: '1.25rem' }}>Treasury Tenor Shocks (bps)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>2Y Treasury Shock:</span>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{rate2y > 0 ? `+${rate2y}` : rate2y} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={rate2y} onChange={(e) => setRate2y(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>5Y Treasury Shock:</span>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{rate5y > 0 ? `+${rate5y}` : rate5y} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={rate5y} onChange={(e) => setRate5y(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>10Y Treasury Shock:</span>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{rate10y > 0 ? `+${rate10y}` : rate10y} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={rate10y} onChange={(e) => setRate10y(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>30Y Treasury Shock:</span>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{rate30y > 0 ? `+${rate30y}` : rate30y} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={rate30y} onChange={(e) => setRate30y(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
            </div>

            <h3 style={{ color: '#e2e8f0', marginBottom: '1.25rem' }}>Credit Spread Shocks (bps)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>Investment Grade (IG):</span>
                  <span style={{ color: '#a855f7', fontWeight: 'bold' }}>{igSpread > 0 ? `+${igSpread}` : igSpread} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={igSpread} onChange={(e) => setIgSpread(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  <span>High Yield (HY):</span>
                  <span style={{ color: '#ec4899', fontWeight: 'bold' }}>{hySpread > 0 ? `+${hySpread}` : hySpread} bps</span>
                </label>
                <input type="range" min="-300" max="300" value={hySpread} onChange={(e) => setHySpread(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <button
                onClick={handleRun}
                disabled={runMutation.isPending}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                {runMutation.isPending ? 'Calculating Revaluation...' : 'Run Stress Test'}
              </button>

              <div style={{ borderTop: '1px solid #334155', paddingTop: '1rem' }}>
                <input
                  type="text"
                  placeholder="Scenario Name (e.g. Fed Hike 2026)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '4px',
                    color: 'white',
                    marginBottom: '0.5rem'
                  }}
                />
                <button
                  onClick={handleSave}
                  disabled={createMutation.isPending}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 'bold'
                  }}
                >
                  Save Scenario to Vault
                </button>
              </div>
            </div>
          </div>

          {/* Results Visuals */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {runResult ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                  <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Base Market Value</div>
                    <div style={{ fontSize: '1.5rem', color: '#e2e8f0', fontWeight: 'bold' }}>
                      ${runResult.base_market_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Stressed Market Value</div>
                    <div style={{ fontSize: '1.5rem', color: '#e2e8f0', fontWeight: 'bold' }}>
                      ${runResult.stressed_market_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Scenario P&L Impact</div>
                    <div style={{ fontSize: '1.5rem', color: runResult.pnl_impact >= 0 ? '#22c55e' : '#ef4444', fontWeight: 'bold' }}>
                      {runResult.pnl_impact >= 0 ? '+' : ''}${runResult.pnl_impact.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
                  <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Position Detail Impact</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', color: '#e2e8f0', fontSize: '0.875rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                          <th style={{ padding: '0.75rem' }}>CUSIP</th>
                          <th style={{ padding: '0.75rem' }}>Quantity</th>
                          <th style={{ padding: '0.75rem' }}>Base Price</th>
                          <th style={{ padding: '0.75rem' }}>Stressed Price</th>
                          <th style={{ padding: '0.75rem' }}>Base MV</th>
                          <th style={{ padding: '0.75rem' }}>Stressed MV</th>
                          <th style={{ padding: '0.75rem' }}>PnL Impact</th>
                        </tr>
                      </thead>
                      <tbody>
                        {runResult.positions.map((p: any) => (
                          <tr key={p.bond_id} style={{ borderBottom: '1px solid #334155' }}>
                            <td style={{ padding: '0.75rem' }}>{p.cusip}</td>
                            <td style={{ padding: '0.75rem' }}>{p.quantity.toLocaleString()}</td>
                            <td style={{ padding: '0.75rem' }}>{p.base_clean_price.toFixed(3)}</td>
                            <td style={{ padding: '0.75rem' }}>{p.stressed_clean_price.toFixed(3)}</td>
                            <td style={{ padding: '0.75rem' }}>${p.base_market_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                            <td style={{ padding: '0.75rem' }}>${p.stressed_market_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                            <td style={{ padding: '0.75rem', color: p.pnl_impact >= 0 ? '#22c55e' : '#ef4444' }}>
                              {p.pnl_impact >= 0 ? '+' : ''}${p.pnl_impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px dotted #334155', color: '#94a3b8' }}>
                Configure shocks on the left and click "Run Stress Test" to revalue.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Saved list */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {loadingScens ? (
            <div style={{ color: '#94a3b8' }}>Loading saved scenarios...</div>
          ) : savedScenarios && savedScenarios.length > 0 ? (
            savedScenarios.map((scen: any) => (
              <div key={scen.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <div>
                  <h3 style={{ color: '#e2e8f0', margin: 0 }}>{scen.name}</h3>
                  <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: '0.25rem 0 0.75rem 0' }}>
                    Created by User {scen.creator_user_id} • Version {scen.version}
                  </p>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                    <span style={{ color: '#38bdf8' }}>2Y: {scen.rate_2y_shock_bps > 0 ? `+${scen.rate_2y_shock_bps}` : scen.rate_2y_shock_bps} bps</span>
                    <span style={{ color: '#38bdf8' }}>5Y: {scen.rate_5y_shock_bps > 0 ? `+${scen.rate_5y_shock_bps}` : scen.rate_5y_shock_bps} bps</span>
                    <span style={{ color: '#38bdf8' }}>10Y: {scen.rate_10y_shock_bps > 0 ? `+${scen.rate_10y_shock_bps}` : scen.rate_10y_shock_bps} bps</span>
                    <span style={{ color: '#38bdf8' }}>30Y: {scen.rate_30y_shock_bps > 0 ? `+${scen.rate_30y_shock_bps}` : scen.rate_30y_shock_bps} bps</span>
                    <span style={{ color: '#a855f7' }}>IG Spread: {scen.ig_spread_shock_bps > 0 ? `+${scen.ig_spread_shock_bps}` : scen.ig_spread_shock_bps} bps</span>
                    <span style={{ color: '#ec4899' }}>HY Spread: {scen.hy_spread_shock_bps > 0 ? `+${scen.hy_spread_shock_bps}` : scen.hy_spread_shock_bps} bps</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => loadScenarioShocks(scen)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 'semibold'
                    }}
                  >
                    Load & Modify
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(scen.id)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 'semibold'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: '#94a3b8' }}>No saved scenarios found. Make one in the Run tab!</div>
          )}
        </div>
      )}
    </div>
  );
};
