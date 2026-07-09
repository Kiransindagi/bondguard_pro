import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  getPortfolioKeyRateDuration,
  getPortfolioBucketedDV01,
  getPortfolioSpreadRisk,
  getPortfolioCarryRollDown,
  getPortfolioPnLExplain
} from '../api/client';
import Plot from 'react-plotly.js';

export const AdvancedRisk = () => {
  const portfolioId = 1;
  const [horizonMonths, setHorizonMonths] = useState(3);

  // States for P&L Explain
  const [rateShock, setRateShock] = useState(25);
  const [spreadShock, setSpreadShock] = useState(50);
  const [actualPnL, setActualPnL] = useState(-15000);

  // Queries
  const { data: krdData, isLoading: loadingKrd } = useQuery({
    queryKey: ['portfolioKrd', portfolioId],
    queryFn: () => getPortfolioKeyRateDuration(portfolioId)
  });

  const { data: dv01Data, isLoading: loadingDv01 } = useQuery({
    queryKey: ['portfolioBucketedDv01', portfolioId],
    queryFn: () => getPortfolioBucketedDV01(portfolioId)
  });

  const { data: spreadData, isLoading: loadingSpread } = useQuery({
    queryKey: ['portfolioSpreadRisk', portfolioId],
    queryFn: () => getPortfolioSpreadRisk(portfolioId)
  });

  const { data: carryData, isLoading: loadingCarry } = useQuery({
    queryKey: ['portfolioCarryRollDown', portfolioId, horizonMonths],
    queryFn: () => getPortfolioCarryRollDown(portfolioId, undefined, horizonMonths)
  });

  const { data: pnlData, isLoading: loadingPnl } = useQuery({
    queryKey: ['portfolioPnLExplain', portfolioId, rateShock, spreadShock, actualPnL],
    queryFn: () => getPortfolioPnLExplain(portfolioId, rateShock, spreadShock, actualPnL)
  });

  const loading = loadingKrd || loadingDv01 || loadingSpread || loadingCarry || loadingPnl;

  if (loading) return <div style={{ color: '#94a3b8' }}>Loading Advanced Fixed-Income Analytics...</div>;

  // Chart 1: Key Rate Durations (KRD)
  const krdKeys = krdData ? Object.keys(krdData.key_rate_durations) : [];
  const krdVals = krdData ? Object.values(krdData.key_rate_durations) : [];

  // Chart 2: Bucketed DV01
  const dv01Keys = dv01Data ? Object.keys(dv01Data.bucketed_dv01) : [];
  const dv01Vals = dv01Data ? Object.values(dv01Data.bucketed_dv01) : [];

  // Chart 3: Sector CS01
  const sectorKeys = spreadData ? Object.keys(spreadData.sector_cs01) : [];
  const sectorVals = spreadData ? Object.values(spreadData.sector_cs01) : [];

  // Waterfall Chart: P&L Explain
  const waterfallData = pnlData ? [
    {
      type: 'waterfall',
      orientation: 'v',
      measure: ['relative', 'relative', 'relative', 'relative', 'total', 'relative', 'total'],
      x: ['Carry', 'Rate Curve PnL', 'Credit Spread PnL', 'Convexity Effect', 'Explained PnL', 'Residual PnL', 'Actual PnL'],
      textposition: 'outside',
      y: [
        pnlData.carry,
        pnlData.rate_pnl,
        pnlData.spread_pnl,
        pnlData.convexity_pnl,
        pnlData.explained_pnl,
        pnlData.residual,
        pnlData.actual_pnl
      ],
      connector: { line: { color: '#475569' } },
      decreasing: { marker: { color: '#ef4444' } },
      increasing: { marker: { color: '#22c55e' } },
      totals: { marker: { color: '#3b82f6' } }
    }
  ] : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Advanced Fixed-Income Risk Analytics</h1>

      {/* Top row: KRD & DV01 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Key Rate Duration (KRD) Profile</h3>
          {krdData && (
            <Plot
              data={[
                {
                  x: krdKeys.map(k => k.replace('KRD_', '')),
                  y: krdVals,
                  type: 'bar',
                  marker: { color: '#38bdf8' }
                }
              ]}
              layout={{
                width: 450,
                height: 300,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#94a3b8' },
                xaxis: { title: 'Tenor' },
                yaxis: { title: 'Duration (Years)' },
                margin: { t: 20, b: 40, l: 45, r: 20 }
              }}
              config={{ displayModeBar: false }}
            />
          )}
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Tenor-Bucketed DV01 Sensitivity</h3>
          {dv01Data && (
            <Plot
              data={[
                {
                  x: dv01Keys.map(k => k.replace('DV01_', '')),
                  y: dv01Vals,
                  type: 'bar',
                  marker: { color: '#f59e0b' }
                }
              ]}
              layout={{
                width: 450,
                height: 300,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#94a3b8' },
                xaxis: { title: 'Tenor' },
                yaxis: { title: 'DV01 ($ / bp)' },
                margin: { t: 20, b: 40, l: 45, r: 20 }
              }}
              config={{ displayModeBar: false }}
            />
          )}
        </div>
      </div>

      {/* Row 2: Credit Spread Risk & Carry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Sector CS01 Spread Sensitivities</h3>
          {spreadData && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <Plot
                data={[
                  {
                    labels: sectorKeys,
                    values: sectorVals,
                    type: 'pie',
                    marker: { colors: ['#a855f7', '#ec4899', '#3b82f6', '#10b981', '#f59e0b'] }
                  }
                ]}
                layout={{
                  width: 450,
                  height: 250,
                  paper_bgcolor: 'transparent',
                  font: { color: '#94a3b8' },
                  margin: { t: 20, b: 20, l: 20, r: 20 }
                }}
                config={{ displayModeBar: false }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '0.875rem', borderTop: '1px solid #334155', paddingTop: '1rem' }}>
                <span style={{ color: '#cbd5e1' }}>Portfolio CS01: <strong>${spreadData.portfolio_cs01}</strong></span>
                <span style={{ color: '#818cf8' }}>IG CS01: <strong>${spreadData.ig_cs01}</strong></span>
                <span style={{ color: '#f43f5e' }}>HY CS01: <strong>${spreadData.hy_cs01}</strong></span>
              </div>
            </div>
          )}
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: '#e2e8f0', margin: 0 }}>Carry & Roll-Down Projections</h3>
            <select
              value={horizonMonths}
              onChange={(e) => setHorizonMonths(Number(e.target.value))}
              style={{
                padding: '0.4rem',
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '4px',
                color: 'white'
              }}
            >
              <option value="1">1 Month</option>
              <option value="3">3 Months</option>
              <option value="6">6 Months</option>
              <option value="12">12 Months</option>
            </select>
          </div>
          {carryData && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Annualized Yield Carry</div>
                  <div style={{ fontSize: '1.25rem', color: '#10b981', fontWeight: 'bold' }}>{carryData.yield_carry.toFixed(2)}%</div>
                </div>
                <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Roll-Down Estimate</div>
                  <div style={{ fontSize: '1.25rem', color: '#10b981', fontWeight: 'bold' }}>{carryData.roll_down_return.toFixed(2)}%</div>
                </div>
              </div>
              <div style={{ backgroundColor: '#334155', padding: '1rem', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ color: '#cbd5e1', fontSize: '0.875rem' }}>Projected Horizon Return ({horizonMonths}m)</div>
                <div style={{ fontSize: '1.75rem', color: '#38bdf8', fontWeight: 'bold', marginTop: '0.25rem' }}>
                  {carryData.projected_return.toFixed(2)}%
                </div>
              </div>
              <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0, fontStyle: 'italic' }}>
                *Note: Carry and roll-down analytics are static calculations assuming unchanged yield curves and credit spreads. They do not constitute actual return forecasts.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Row 3: P&L Explain */}
      <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '1.5rem' }}>Deterministic P&L Attribution Explain</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
          {/* Inputs */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                Rate Curve Shock (bps): <strong>{rateShock > 0 ? `+${rateShock}` : rateShock} bps</strong>
              </label>
              <input type="range" min="-100" max="100" value={rateShock} onChange={(e) => setRateShock(Number(e.target.value))} style={{ width: '100%' }} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                Credit Spread Shock (bps): <strong>{spreadShock > 0 ? `+${spreadShock}` : spreadShock} bps</strong>
              </label>
              <input type="range" min="-150" max="150" value={spreadShock} onChange={(e) => setSpreadShock(Number(e.target.value))} style={{ width: '100%' }} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                Actual Observed P&L ($): <strong>${actualPnL.toLocaleString()}</strong>
              </label>
              <input type="range" min="-50000" max="50000" step="1000" value={actualPnL} onChange={(e) => setActualPnL(Number(e.target.value))} style={{ width: '100%' }} />
            </div>
          </div>

          {/* Waterfall Visual */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            {pnlData && (
              <Plot
                data={waterfallData}
                layout={{
                  width: 600,
                  height: 350,
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#94a3b8' },
                  yaxis: { title: 'P&L ($)' },
                  margin: { t: 20, b: 40, l: 60, r: 20 }
                }}
                config={{ displayModeBar: false }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
