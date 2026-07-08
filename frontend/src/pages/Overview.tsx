
import { useQuery } from '@tanstack/react-query';
import { fetchPortfolioSummary, fetchPortfolioRiskSummary, getPortfolioRiskReport, getSnapshots } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

export const Overview = () => {
  const portfolioId = 1;

  const { data: summary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['portfolioSummary', portfolioId],
    queryFn: () => fetchPortfolioSummary(portfolioId)
  });

  const { data: riskSummary, isLoading: isRiskLoading } = useQuery({
    queryKey: ['portfolioRiskSummary', portfolioId],
    queryFn: () => fetchPortfolioRiskSummary(portfolioId)
  });

  const { data: report, isLoading: isReportLoading } = useQuery({
    queryKey: ['riskReport', portfolioId],
    queryFn: () => getPortfolioRiskReport(portfolioId)
  });

  const { data: snapshots, isLoading: isSnapshotsLoading } = useQuery({
    queryKey: ['snapshots', portfolioId],
    queryFn: () => getSnapshots(portfolioId)
  });

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', color: '#e2e8f0' }}>Dashboard Overview</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {/* Portfolio Stats */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Portfolio</h3>
          {isSummaryLoading ? <div>Loading...</div> : summary ? (
            <>
              <div style={{ fontSize: '1.5rem', color: '#e2e8f0', marginBottom: '0.5rem' }}>${Number(summary.total_market_value).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
              <div style={{ color: summary.total_pnl >= 0 ? '#22c55e' : '#ef4444' }}>
                Unrealized PnL: {summary.total_pnl >= 0 ? '+' : ''}{Number(summary.total_pnl).toLocaleString(undefined, {minimumFractionDigits: 2})}
              </div>
            </>
          ) : <div>Data unavailable</div>}
        </div>

        {/* Risk Stats */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Duration Risk</h3>
          {isRiskLoading ? <div>Loading...</div> : riskSummary ? (
            <>
              <div style={{ fontSize: '1.5rem', color: '#e2e8f0', marginBottom: '0.5rem' }}>
                {Number(riskSummary.weighted_modified_duration).toFixed(2)} yrs
              </div>
              <div style={{ color: '#e2e8f0' }}>DV01: ${Number(riskSummary.total_dv01).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
            </>
          ) : <div>Data unavailable</div>}
        </div>

        {/* Market Risk */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Market Risk</h3>
          {isReportLoading ? <div>Loading...</div> : report && report.market_risk ? (
            <>
              <div style={{ fontSize: '1.5rem', color: '#e2e8f0', marginBottom: '0.5rem' }}>
                VaR: {report.market_risk.historical_var !== null ? '$' + Number(report.market_risk.historical_var).toLocaleString(undefined, {minimumFractionDigits: 2}) : 'N/A'}
              </div>
              <div style={{ color: '#e2e8f0' }}>
                ES: {report.market_risk.expected_shortfall !== null ? '$' + Number(report.market_risk.expected_shortfall).toLocaleString(undefined, {minimumFractionDigits: 2}) : 'N/A'}
              </div>
            </>
          ) : <div>Data unavailable</div>}
        </div>

        {/* Risk Control */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Risk Control</h3>
          {isReportLoading ? <div>Loading...</div> : report && report.limit_summary ? (
            <>
              <div style={{ fontSize: '1.5rem', color: report.report_metadata.overall_status === 'BREACH' ? '#ef4444' : report.report_metadata.overall_status === 'WARNING' ? '#eab308' : '#22c55e', marginBottom: '0.5rem' }}>
                {report.report_metadata.overall_status}
              </div>
              <div style={{ color: '#e2e8f0' }}>
                <span style={{ color: '#ef4444', marginRight: '0.5rem' }}>{report.breach_summary.open_count} Open Breaches</span>
              </div>
            </>
          ) : <div>Data unavailable</div>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
           <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Stress Testing</h3>
           {isReportLoading && <div>Loading...</div>}
           {!isReportLoading && !report && <div>Data unavailable</div>}
           {report && report.stress_risk && (
             <div>
               <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#94a3b8' }}>
                 <span>Worst Scenario</span>
                 <span style={{ color: '#e2e8f0' }}>{report.stress_risk.worst_scenario_name || 'N/A'}</span>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                 <span>Worst Loss</span>
                 <span style={{ color: '#ef4444' }}>{report.stress_risk.pnl !== null ? '-$' + Math.abs(Number(report.stress_risk.pnl)).toLocaleString(undefined, {minimumFractionDigits: 2}) : 'N/A'}</span>
               </div>
             </div>
           )}
        </div>
        
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
           <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Liquidity Profile</h3>
           {isReportLoading && <div>Loading...</div>}
           {!isReportLoading && !report && <div>Data unavailable</div>}
           {report && report.liquidity_risk && (
             <div>
               <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#94a3b8' }}>
                 <span>Liquidity Score</span>
                 <span style={{ color: '#e2e8f0' }}>{report.liquidity_risk.liquidity_score !== null ? Number(report.liquidity_risk.liquidity_score).toFixed(2) : 'N/A'} / 100</span>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                 <span>Largest Concentration</span>
                 <span style={{ color: '#e2e8f0' }}>{report.concentration.largest_issuer || 'N/A'} ({(Number(report.concentration.largest_issuer_weight || 0) * 100).toFixed(1)}%)</span>
               </div>
             </div>
           )}
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
           <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Model Governance</h3>
           {isReportLoading && <div>Loading...</div>}
           {!isReportLoading && !report && <div>Data unavailable</div>}
           {report && report.model_governance && (
             <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#94a3b8' }}>
                 <span>Market Risk Model</span>
                 <span style={{ color: report.market_risk.model_status === 'RATE_ONLY_MODEL' ? '#f59e0b' : '#22c55e' }}>{report.market_risk.model_status}</span>
               </div>
                {report.model_governance.degraded_models.map((m: string) => (
                  <div key={m} style={{ color: '#eab308', marginBottom: '0.5rem', fontSize: '0.875rem' }}>⚠️ {m} is Degraded</div>
                ))}
                {report.model_governance.proxy_models.map((m: string) => (
                  <div key={m} style={{ color: '#38bdf8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>ℹ️ {m} (Proxy Active)</div>
                ))}
             </div>
           )}
        </div>
      </div>

      {/* Historical Trend Charts */}
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#e2e8f0' }}>Historical Risk Trends</h2>
      
      {isSnapshotsLoading ? <div style={{ color: '#94a3b8' }}>Loading historical data...</div> : (!snapshots || snapshots.length <= 1) ? (
        <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '8px', textAlign: 'center', color: '#94a3b8' }}>
          Historical trend requires additional snapshots.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          
          <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: '#e2e8f0', marginBottom: '1rem', textAlign: 'center' }}>Portfolio Market Value</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="snapshot_date" stroke="#94a3b8" tick={{fontSize: 12}} />
                <YAxis stroke="#94a3b8" tick={{fontSize: 12}} tickFormatter={(val: any) => `$${(val/1000000).toFixed(1)}M`} />
                <RechartsTooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}} />
                <Line type="monotone" dataKey="total_market_value" name="Market Value" stroke="#3b82f6" strokeWidth={2} dot={{r: 3}} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: '#e2e8f0', marginBottom: '1rem', textAlign: 'center' }}>Modified Duration</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="snapshot_date" stroke="#94a3b8" tick={{fontSize: 12}} />
                <YAxis stroke="#94a3b8" tick={{fontSize: 12}} domain={['auto', 'auto']} />
                <RechartsTooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}} />
                <Line type="monotone" dataKey="weighted_modified_duration" name="Mod Dur (yrs)" stroke="#10b981" strokeWidth={2} dot={{r: 3}} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: '#e2e8f0', marginBottom: '1rem', textAlign: 'center' }}>Total DV01</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="snapshot_date" stroke="#94a3b8" tick={{fontSize: 12}} />
                <YAxis stroke="#94a3b8" tick={{fontSize: 12}} />
                <RechartsTooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}} />
                <Line type="monotone" dataKey="total_dv01" name="DV01" stroke="#f59e0b" strokeWidth={2} dot={{r: 3}} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: '#e2e8f0', marginBottom: '1rem', textAlign: 'center' }}>VaR (95%) & Breach Count</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="snapshot_date" stroke="#94a3b8" tick={{fontSize: 12}} />
                <YAxis yAxisId="left" stroke="#8b5cf6" tick={{fontSize: 12}} />
                <YAxis yAxisId="right" orientation="right" stroke="#ef4444" tick={{fontSize: 12}} />
                <RechartsTooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="historical_var_95_1d" name="VaR 95%" stroke="#8b5cf6" strokeWidth={2} dot={{r: 3}} connectNulls />
                <Line yAxisId="right" type="monotone" dataKey="open_breach_count" name="Open Breaches" stroke="#ef4444" strokeWidth={2} dot={{r: 3}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
        </div>
      )}

    </div>
  );
};
