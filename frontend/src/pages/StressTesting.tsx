import React, { useState, useEffect } from 'react';
import { fetchScenarios, runStressTest, compareScenarios } from '../api/stressTesting';
import type { StressScenario, StressRunResponse, StressComparisonResponse } from '../api/stressTesting';
import { AlertCircle, Play, BarChart2 } from 'lucide-react';

export const StressTesting: React.FC = () => {
  const [scenarios, setScenarios] = useState<StressScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<StressRunResponse | null>(null);
  const [comparisonResult, setComparisonResult] = useState<StressComparisonResponse | null>(null);
  
  const portfolioId = 1;

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await fetchScenarios();
      setScenarios(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load scenarios');
    }
  };

  const handleRunScenario = async () => {
    if (selectedScenarioId === '') return;
    setLoading(true);
    setError(null);
    setComparisonResult(null);
    try {
      const res = await runStressTest(portfolioId, selectedScenarioId as number);
      setRunResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to run scenario');
    } finally {
      setLoading(false);
    }
  };

  const handleCompareAll = async () => {
    setLoading(true);
    setError(null);
    setRunResult(null);
    try {
      const predefinedIds = scenarios.filter(s => s.is_predefined).map(s => s.id);
      const idsToCompare = predefinedIds.slice(0, 5); 
      const res = await compareScenarios(portfolioId, idsToCompare);
      setComparisonResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compare scenarios');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div style={{ padding: '24px', color: '#f1f5f9' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <BarChart2 />
        Stress Testing & Scenario Analysis
      </h1>
      
      {error && (
        <div style={{ padding: '16px', backgroundColor: '#7f1d1d', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}
      
      <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px', marginBottom: '24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <select 
          value={selectedScenarioId} 
          onChange={(e) => setSelectedScenarioId(Number(e.target.value))}
          style={{ padding: '12px', borderRadius: '4px', backgroundColor: '#0f172a', color: '#f1f5f9', border: '1px solid #334155', flex: 1 }}
        >
          <option value="">Select Scenario</option>
          {scenarios.map((scen) => (
            <option key={scen.id} value={scen.id}>
              {scen.name} - {scen.scenario_type.replace('_', ' ')}
            </option>
          ))}
        </select>
        
        <button 
          onClick={handleRunScenario} 
          disabled={loading || selectedScenarioId === ''}
          style={{ padding: '12px 24px', borderRadius: '4px', backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: (loading || selectedScenarioId === '') ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Play size={16} /> Run Scenario
        </button>
        
        <button 
          onClick={handleCompareAll} 
          disabled={loading}
          style={{ padding: '12px 24px', borderRadius: '4px', backgroundColor: 'transparent', color: '#38bdf8', border: '1px solid #38bdf8', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          Compare Top 5
        </button>
      </div>
      
      {loading && <div style={{ color: '#94a3b8', textAlign: 'center', padding: '40px' }}>Running calculations...</div>}

      {runResult && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Total P&L</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: runResult.total_pnl < 0 ? '#ef4444' : '#22c55e' }}>
                {formatCurrency(runResult.total_pnl)}
              </div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Loss %</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: runResult.total_loss_percent < 0 ? '#ef4444' : '#22c55e' }}>
                {formatPercent(runResult.total_loss_percent)}
              </div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Base Market Value</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {formatCurrency(runResult.base_market_value)}
              </div>
            </div>
            <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>Stressed Market Value</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {formatCurrency(runResult.stressed_market_value)}
              </div>
            </div>
          </div>
          
          <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Position Attribution</h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '12px' }}>Bond</th>
                    <th style={{ padding: '12px' }}>Rating</th>
                    <th style={{ padding: '12px' }}>Base Price</th>
                    <th style={{ padding: '12px' }}>Stressed Price</th>
                    <th style={{ padding: '12px' }}>Rate Shock (bps)</th>
                    <th style={{ padding: '12px' }}>Spread Shock (bps)</th>
                    <th style={{ padding: '12px' }}>PnL</th>
                    <th style={{ padding: '12px' }}>Contrib %</th>
                  </tr>
                </thead>
                <tbody>
                  {runResult.positions.map(pos => (
                    <tr key={pos.id} style={{ borderBottom: '1px solid #334155' }}>
                      <td style={{ padding: '12px' }}>{pos.bond_name}</td>
                      <td style={{ padding: '12px' }}>{pos.rating}</td>
                      <td style={{ padding: '12px' }}>{pos.base_clean_price.toFixed(2)}</td>
                      <td style={{ padding: '12px' }}>{pos.stressed_clean_price.toFixed(2)}</td>
                      <td style={{ padding: '12px' }}>{pos.rate_shock_bps.toFixed(1)}</td>
                      <td style={{ padding: '12px' }}>{pos.spread_shock_bps.toFixed(1)}</td>
                      <td style={{ padding: '12px', color: pos.pnl < 0 ? '#ef4444' : '#22c55e' }}>{formatCurrency(pos.pnl)}</td>
                      <td style={{ padding: '12px' }}>{pos.contribution_percent.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {comparisonResult && (
        <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Scenario Comparison</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '12px' }}>Scenario</th>
                  <th style={{ padding: '12px' }}>Total PnL</th>
                  <th style={{ padding: '12px' }}>Loss %</th>
                  <th style={{ padding: '12px' }}>Method</th>
                </tr>
              </thead>
              <tbody>
                {comparisonResult.scenarios.map((scen, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '12px' }}>{scen.scenario_name}</td>
                    <td style={{ padding: '12px', color: scen.total_pnl < 0 ? '#ef4444' : '#22c55e' }}>{formatCurrency(scen.total_pnl)}</td>
                    <td style={{ padding: '12px', color: scen.total_loss_percent < 0 ? '#ef4444' : '#22c55e' }}>{formatPercent(scen.total_loss_percent)}</td>
                    <td style={{ padding: '12px' }}>{scen.calculation_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default StressTesting;
