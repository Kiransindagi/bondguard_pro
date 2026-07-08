import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { AlertCircle, Droplets } from 'lucide-react';
import { apiClient } from '../api/client';

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

  const portfolioId = 1;

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const sumRes = await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/summary`);
      setSummary(sumRes.data);

      const posRes = await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/positions`);
      setPositions(posRes.data);

      const limRes = await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/limits`);
      setLimits(limRes.data);

      const varRes = await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/liquidity-adjusted-var`);
      setVarData(varRes.data);

      await loadConcentration(dimension);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadConcentration = async (dim: string) => {
    try {
      const res = await apiClient.get(`/liquidity-risk/portfolios/${portfolioId}/concentration?dimension=${dim}`);
      setConcentration(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const runSnapshot = async () => {
    setLoading(true);
    try {
      await apiClient.post(`/liquidity-risk/portfolios/${portfolioId}/snapshot`);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to run snapshot');
      setLoading(false);
    }
  };

  const runStress = async (sc: string) => {
    setScenario(sc);
    if (sc === 'NORMAL') {
      setStressData(null);
      return;
    }
    try {
      const res = await apiClient.post(`/liquidity-risk/portfolios/${portfolioId}/stress`, { scenario: sc });
      setStressData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (summary) {
      loadConcentration(dimension);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dimension]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
  };

  return (
    <div style={{ padding: '24px', color: '#f1f5f9' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Droplets />
        Liquidity Risk & Concentration
      </h1>

      <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Analyze market liquidity, transaction costs, and portfolio concentration.</span>
        <button 
          onClick={runSnapshot} 
          disabled={loading}
          style={{ padding: '8px 16px', borderRadius: '4px', backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Running...' : 'Generate New Snapshot'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '16px', backgroundColor: '#7f1d1d', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {summary && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Portfolio Market Value</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{formatCurrency(summary.portfolio_market_value)}</div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Liquidity Score (0-100)</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8' }}>{summary.weighted_liquidity_score.toFixed(1)}</div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Liquidation Cost</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>{formatCurrency(summary.estimated_total_liquidation_cost)}</div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>{summary.estimated_total_liquidation_cost_bps.toFixed(2)} bps</div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Days to Liquidate</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{summary.weighted_days_to_liquidate.toFixed(1)}</div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>Max: {summary.maximum_days_to_liquidate}</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
              <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Liquidation Horizon Distribution</h2>
              <Plot
                data={[
                  {
                    x: summary.liquidation_horizon_distribution.map((d: any) => d.bucket.replace(/_/g, ' ')),
                    y: summary.liquidation_horizon_distribution.map((d: any) => d.market_value),
                    type: 'bar',
                    marker: { color: '#8b5cf6' }
                  }
                ]}
                layout={{
                  height: 300,
                  margin: { t: 10, r: 10, l: 50, b: 40 },
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  font: { color: '#94a3b8' },
                  yaxis: { gridcolor: '#334155' },
                  xaxis: { tickangle: -20 }
                }}
                config={{ displayModeBar: false }}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '18px' }}>Concentration Analytics</h2>
                <select 
                  value={dimension} 
                  onChange={(e) => setDimension(e.target.value)}
                  style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#0f172a', color: '#f1f5f9', border: '1px solid #334155' }}
                >
                  <option value="issuer">Issuer</option>
                  <option value="sector">Sector</option>
                  <option value="country">Country</option>
                  <option value="rating">Rating</option>
                  <option value="maturity">Maturity</option>
                </select>
              </div>
              {concentration && (
                <Plot
                  data={[
                    {
                      x: concentration.breakdown.slice(0, 10).map((d: any) => d.name),
                      y: concentration.breakdown.slice(0, 10).map((d: any) => d.market_value),
                      type: 'bar',
                      marker: { color: '#10b981' }
                    }
                  ]}
                  layout={{
                    height: 300,
                    margin: { t: 10, r: 10, l: 50, b: 40 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#94a3b8' },
                    yaxis: { gridcolor: '#334155' },
                    xaxis: { tickangle: -20 }
                  }}
                  config={{ displayModeBar: false }}
                  style={{ width: '100%' }}
                />
              )}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
              <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Liquidity-Adjusted VaR</h2>
              {varData ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #334155' }}>
                    <span style={{ color: '#94a3b8' }}>Market VaR</span>
                    <span style={{ fontWeight: 'bold' }}>{formatCurrency(varData.market_var)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #334155' }}>
                    <span style={{ color: '#94a3b8' }}>Liquidation Cost Adjustment</span>
                    <span style={{ fontWeight: 'bold', color: '#ef4444' }}>+{formatCurrency(varData.liquidity_cost_adjustment)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 0', fontSize: '18px' }}>
                    <span>Liquidity-Adjusted VaR</span>
                    <span style={{ fontWeight: 'bold', color: '#ef4444' }}>{formatCurrency(varData.liquidity_adjusted_var)}</span>
                  </div>
                  {varData.market_risk_model_status === 'RATE_ONLY_MODEL' && (
                    <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#0f172a', borderRadius: '4px', borderLeft: '4px solid #f59e0b', fontSize: '14px', color: '#cbd5e1' }}>
                      {varData.limitations}
                    </div>
                  )}
                </div>
              ) : <div>Loading...</div>}
            </div>

            <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '18px' }}>Liquidity Stress Testing</h2>
                <select 
                  value={scenario} 
                  onChange={(e) => runStress(e.target.value)}
                  style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#0f172a', color: '#f1f5f9', border: '1px solid #334155' }}
                >
                  <option value="NORMAL">Normal Scenario</option>
                  <option value="MODERATE">Moderate Stress</option>
                  <option value="SEVERE">Severe Stress</option>
                  <option value="CREDIT_MARKET_FREEZE">Credit Market Freeze</option>
                </select>
              </div>
              
              {stressData ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #334155' }}>
                    <span style={{ color: '#94a3b8' }}>Normal Liquidation Cost</span>
                    <span>{formatCurrency(stressData.normal_liquidation_cost)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #334155' }}>
                    <span style={{ color: '#94a3b8' }}>Stressed Liquidation Cost</span>
                    <span style={{ fontWeight: 'bold', color: '#ef4444' }}>{formatCurrency(stressData.stressed_liquidation_cost)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #334155' }}>
                    <span style={{ color: '#94a3b8' }}>Normal Days to Liquidate</span>
                    <span>{stressData.normal_days_to_liquidate.toFixed(1)} days</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                    <span style={{ color: '#94a3b8' }}>Stressed Days to Liquidate</span>
                    <span style={{ fontWeight: 'bold', color: '#ef4444' }}>{stressData.stressed_days_to_liquidate.toFixed(1)} days</span>
                  </div>
                </div>
              ) : (
                <div style={{ color: '#94a3b8', padding: '24px 0', textAlign: 'center' }}>
                  Select a stress scenario to view estimated liquidity impact.
                </div>
              )}
            </div>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Concentration Limits</h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '12px' }}>Limit Type</th>
                    <th style={{ padding: '12px' }}>Threshold</th>
                    <th style={{ padding: '12px' }}>Warning</th>
                    <th style={{ padding: '12px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {limits.length > 0 ? limits.map((lim, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #334155' }}>
                      <td style={{ padding: '12px' }}>{lim.limit.limit_type.replace(/_/g, ' ')}</td>
                      <td style={{ padding: '12px' }}>{(lim.limit.threshold_value * 100).toFixed(1)}%</td>
                      <td style={{ padding: '12px' }}>{(lim.limit.warning_threshold_value * 100).toFixed(1)}%</td>
                      <td style={{ padding: '12px', fontWeight: 'bold', color: lim.status === 'OK' ? '#10b981' : lim.status === 'WARNING' ? '#f59e0b' : '#ef4444' }}>
                        {lim.status}
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan={4} style={{ padding: '12px', textAlign: 'center' }}>No limits configured.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Position Liquidity Details</h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '12px' }}>Bond</th>
                    <th style={{ padding: '12px' }}>Class</th>
                    <th style={{ padding: '12px' }}>Score</th>
                    <th style={{ padding: '12px' }}>Spread (bps)</th>
                    <th style={{ padding: '12px' }}>Est. Cost</th>
                    <th style={{ padding: '12px' }}>Days to Liq.</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.position_id} style={{ borderBottom: '1px solid #334155' }}>
                      <td style={{ padding: '12px' }}>{pos.bond_name}</td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ 
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          backgroundColor: pos.liquidity_class === 'HIGH' ? '#10b98122' : pos.liquidity_class === 'MEDIUM' ? '#3b82f622' : '#f59e0b22',
                          color: pos.liquidity_class === 'HIGH' ? '#10b981' : pos.liquidity_class === 'MEDIUM' ? '#3b82f6' : '#f59e0b'
                        }}>
                          {pos.liquidity_class}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>{pos.liquidity_score.toFixed(1)}</td>
                      <td style={{ padding: '12px' }}>{pos.estimated_bid_ask_bps.toFixed(1)}</td>
                      <td style={{ padding: '12px' }}>{formatCurrency(pos.estimated_liquidation_cost)}</td>
                      <td style={{ padding: '12px' }}>{pos.estimated_trading_days_to_liquidate}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
