import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLatestAnalytics, getAnalyticsHistory, triggerAnalyticsRun } from '../api/client';

export const AnalyticsRuns = () => {
  const queryClient = useQueryClient();
  const [portfolioId] = useState<number>(1); // Global fixed income core portfolio
  const [valuationDate, setValuationDate] = useState<string>(new Date().toISOString().split('T')[0]);

  // Latest batch evaluation & snapshot
  const { data: latest, isLoading: isLatestLoading, isError: isLatestError, refetch: refetchLatest } = useQuery({
    queryKey: ['latestAnalytics', portfolioId],
    queryFn: () => getLatestAnalytics(portfolioId),
  });

  // Analytics runs history
  const { data: history, isLoading: isHistoryLoading, refetch: refetchHistory } = useQuery({
    queryKey: ['analyticsHistory', portfolioId],
    queryFn: () => getAnalyticsHistory(portfolioId),
  });

  const mutation = useMutation({
    mutationFn: (dateVal: string) => triggerAnalyticsRun(portfolioId, dateVal),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['latestAnalytics', portfolioId] });
      queryClient.invalidateQueries({ queryKey: ['analyticsHistory', portfolioId] });
    },
  });

  const handleTriggerRun = () => {
    mutation.mutate(valuationDate);
  };

  const handleRefresh = () => {
    refetchLatest();
    refetchHistory();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Analytics Runs</h1>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input 
            type="date"
            value={valuationDate}
            onChange={(e) => setValuationDate(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: '#1e293b', 
              color: '#cbd5e1', 
              border: '1px solid #334155', 
              borderRadius: '4px',
              cursor: 'pointer' 
            }}
          />
          <button 
            onClick={handleTriggerRun}
            disabled={mutation.isPending}
            style={{ 
              padding: '0.5rem 1rem', 
              backgroundColor: '#3b82f6', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: mutation.isPending ? 'not-allowed' : 'pointer',
              opacity: mutation.isPending ? 0.6 : 1
            }}
          >
            {mutation.isPending ? 'Calculating...' : 'Run Valuation Batch'}
          </button>
          <button 
            onClick={handleRefresh}
            style={{ padding: '0.5rem 1rem', backgroundColor: '#475569', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Refresh
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        
        {/* Latest Batch Snapshot Report */}
        <div>
          <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Latest Valuation Summary</h2>
          {isLatestLoading ? (
            <p style={{ color: '#94a3b8' }}>Loading latest snapshot...</p>
          ) : isLatestError || !latest || !latest.snapshot ? (
            <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
              <p style={{ color: '#94a3b8' }}>No batch evaluations have been run for this portfolio yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Status Header Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Valuation Status</span>
                  <div style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: 'bold', 
                    color: latest.run.status === 'SUCCESS' ? '#22c55e' : latest.run.status === 'PARTIAL_SUCCESS' ? '#eab308' : '#ef4444',
                    marginTop: '0.25rem'
                  }}>
                    {latest.run.status}
                  </div>
                </div>
                <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Model Status</span>
                  <div style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: 'bold', 
                    color: latest.snapshot.market_risk_model_status === 'FULL_FACTOR_MODEL' ? '#22c55e' : latest.snapshot.market_risk_model_status === 'RATE_ONLY_MODEL' ? '#eab308' : '#ef4444',
                    marginTop: '0.25rem'
                  }}>
                    {latest.snapshot.market_risk_model_status.replace('_', ' ')}
                  </div>
                </div>
                <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Data Quality Status</span>
                  <div style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: 'bold', 
                    color: latest.run.data_quality_status === 'PASS' ? '#22c55e' : latest.run.data_quality_status === 'WARNING' ? '#eab308' : '#ef4444',
                    marginTop: '0.25rem'
                  }}>
                    {latest.run.data_quality_status}
                  </div>
                </div>
              </div>

              {/* Snapshot Statistics */}
              <div style={{ padding: '1.25rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 1rem 0', color: '#38bdf8', fontSize: '1.1rem' }}>Metrics Snapshot</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Market Value:</span>
                      <span style={{ color: '#f1f5f9', fontWeight: 'bold' }}>
                        ${Number(latest.snapshot.total_market_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Unrealized P&L:</span>
                      <span style={{ color: Number(latest.snapshot.total_unrealized_pnl) >= 0 ? '#22c55e' : '#ef4444' }}>
                        ${Number(latest.snapshot.total_unrealized_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Portfolio YTM:</span>
                      <span style={{ color: '#f1f5f9' }}>{(latest.snapshot.weighted_ytm * 100).toFixed(2)}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Modified Duration:</span>
                      <span style={{ color: '#f1f5f9' }}>{latest.snapshot.weighted_modified_duration.toFixed(2)} yrs</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Total DV01:</span>
                      <span style={{ color: '#f1f5f9' }}>${Number(latest.snapshot.total_dv01).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Historical VaR (95% 1D):</span>
                      <span style={{ color: '#f1f5f9' }}>
                        {latest.snapshot.historical_var_95_1d ? `$${Number(latest.snapshot.historical_var_95_1d).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Expected Shortfall (95%):</span>
                      <span style={{ color: '#f1f5f9' }}>
                        {latest.snapshot.expected_shortfall_95_1d ? `$${Number(latest.snapshot.expected_shortfall_95_1d).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Liquidity Score:</span>
                      <span style={{ color: '#f1f5f9' }}>{latest.snapshot.weighted_liquidity_score ? `${latest.snapshot.weighted_liquidity_score.toFixed(2)} / 100` : 'N/A'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Liquidation Cost:</span>
                      <span style={{ color: '#f1f5f9' }}>
                        {latest.snapshot.liquidation_cost ? `$${Number(latest.snapshot.liquidation_cost).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Limits Breach Status:</span>
                      <span style={{ 
                        color: latest.snapshot.overall_limit_status === 'PASS' ? '#22c55e' : latest.snapshot.overall_limit_status === 'WARNING' ? '#eab308' : '#ef4444',
                        fontWeight: 'bold'
                      }}>
                        {latest.snapshot.overall_limit_status} ({latest.snapshot.open_breach_count} Breaches)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Limitations & Metadata Context */}
        <div>
          <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Valuation Context</h2>
          {latest && latest.run && (
            <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
                <span style={{ color: '#94a3b8' }}>As of Date:</span>
                <span style={{ color: '#cbd5e1', fontWeight: 'bold' }}>{latest.run.valuation_date}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
                <span style={{ color: '#94a3b8' }}>Calculated At:</span>
                <span style={{ color: '#cbd5e1' }}>{new Date(latest.run.started_at).toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
                <span style={{ color: '#94a3b8' }}>Market Data Date:</span>
                <span style={{ color: '#cbd5e1' }}>{latest.run.metadata_json?.market_data_as_of || 'N/A'}</span>
              </div>
              
              <div style={{ marginTop: '0.5rem' }}>
                <span style={{ color: '#94a3b8', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Model Governance Warnings:</span>
                {!latest.run.metadata_json?.degraded_models || latest.run.metadata_json.degraded_models.length === 0 ? (
                  <span style={{ color: '#22c55e', fontSize: '0.9rem' }}>✓ All risk factor models fully aligned.</span>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    {latest.run.metadata_json.degraded_models.map((m: string) => (
                      <span key={m} style={{ color: '#eab308', fontSize: '0.85rem' }}>⚠️ {m} has degraded status</span>
                    ))}
                  </div>
                )}
              </div>

              {latest.run.error_summary && (
                <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#7f1d1d', borderRadius: '4px', border: '1px solid #b91c1c' }}>
                  <span style={{ color: '#fca5a5', fontSize: '0.85rem', fontWeight: 'bold' }}>Batch run warnings:</span>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#fef2f2', fontSize: '0.8rem' }}>{latest.run.error_summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Runs History */}
      <div>
        <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Runs History</h2>
        {isHistoryLoading ? (
          <p style={{ color: '#94a3b8' }}>Loading runs history...</p>
        ) : !history || history.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>No batch evaluations have been recorded.</p>
        ) : (
          <div style={{ backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#cbd5e1', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#0f172a', borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem' }}>Run ID</th>
                  <th style={{ padding: '0.75rem' }}>Valuation Date</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Model Status</th>
                  <th style={{ padding: '0.75rem' }}>Quality Status</th>
                  <th style={{ padding: '0.75rem' }}>Run Time</th>
                  <th style={{ padding: '0.75rem' }}>Diagnostic Summary</th>
                </tr>
              </thead>
              <tbody>
                {history.map((run: any) => (
                  <tr key={run.id} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>#{run.id}</td>
                    <td style={{ padding: '0.75rem' }}>{run.valuation_date}</td>
                    <td style={{ 
                      padding: '0.75rem',
                      color: run.status === 'SUCCESS' ? '#22c55e' : run.status === 'PARTIAL_SUCCESS' ? '#eab308' : '#ef4444',
                      fontWeight: 'bold'
                    }}>
                      {run.status}
                    </td>
                    <td style={{ padding: '0.75rem' }}>{run.model_status || 'N/A'}</td>
                    <td style={{ padding: '0.75rem' }}>{run.data_quality_status || 'N/A'}</td>
                    <td style={{ padding: '0.75rem' }}>{new Date(run.started_at).toLocaleString()}</td>
                    <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: '#94a3b8', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {run.error_summary || 'Calculation processed successfully.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
export default AnalyticsRuns;
