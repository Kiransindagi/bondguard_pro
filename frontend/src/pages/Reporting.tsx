
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSnapshots, getExecutiveReport, generateSnapshot } from '../api/client';


export const Reporting = () => {
  const queryClient = useQueryClient();
  const portfolioId = 1;

  const { data: snapshots, isLoading: snapsLoading } = useQuery({
    queryKey: ['snapshots', portfolioId],
    queryFn: () => getSnapshots(portfolioId)
  });

  const { data: latestReport, isLoading: reportLoading } = useQuery({
    queryKey: ['executiveReport', portfolioId],
    queryFn: () => getExecutiveReport(portfolioId)
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSnapshot(portfolioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots', portfolioId] });
      queryClient.invalidateQueries({ queryKey: ['executiveReport', portfolioId] });
      alert("Snapshot generated successfully.");
    },
    onError: (err) => {
      alert("Error generating snapshot: " + err);
    }
  });

  if (snapsLoading || reportLoading) return <div style={{ color: '#94a3b8' }}>Loading Reporting...</div>;

  const handleDownloadCsv = () => {
    window.open(`http://localhost:8000/api/v1/reporting/portfolios/${portfolioId}/executive-report.csv`, '_blank');
  };

  const handleDownloadPdf = () => {
    window.open(`http://localhost:8000/api/v1/reporting/portfolios/${portfolioId}/executive-report.pdf`, '_blank');
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Institutional Reporting</h1>
        <div>
          <button 
            onClick={() => generateMutation.mutate()} 
            disabled={generateMutation.isPending}
            style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '1rem' }}
          >
            {generateMutation.isPending ? 'Generating...' : 'Generate Today\'s Snapshot'}
          </button>
          <button onClick={handleDownloadCsv} style={{ padding: '0.5rem 1rem', backgroundColor: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '1rem' }}>CSV Export</button>
          <button onClick={handleDownloadPdf} style={{ padding: '0.5rem 1rem', backgroundColor: '#ef4444', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>PDF Report</button>
        </div>
      </div>

      <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>Historical risk monitoring and executive PDF generation.</p>

      {latestReport && latestReport.executive_summary && (
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.25rem', color: '#e2e8f0', marginTop: 0 }}>Latest Executive Summary</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Overall Status</div>
              <div style={{ fontSize: '1.25rem', color: latestReport.executive_summary.overall_risk_status === 'PASS' ? '#22c55e' : '#ef4444' }}>{latestReport.executive_summary.overall_risk_status}</div>
            </div>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Open Breaches</div>
              <div style={{ fontSize: '1.25rem', color: '#e2e8f0' }}>{latestReport.executive_summary.number_of_open_breaches}</div>
            </div>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Model Status</div>
              <div style={{ fontSize: '1.25rem', color: latestReport.executive_summary.market_risk_model_status === 'RATE_ONLY_MODEL' ? '#f59e0b' : '#22c55e' }}>{latestReport.executive_summary.market_risk_model_status}</div>
            </div>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Largest Contributor</div>
              <div style={{ fontSize: '1.25rem', color: '#e2e8f0' }}>{latestReport.executive_summary.largest_risk_contributor}</div>
            </div>
          </div>
          
          <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#451a03', color: '#fcd34d', borderRadius: '4px' }}>
            <strong>Model Governance & Limitations:</strong>
            <ul style={{ margin: 0, paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
              {latestReport.model_governance?.limitations?.map((l: string, i: number) => <li key={i}>{l}</li>) || <li>No current limitations.</li>}
            </ul>
          </div>
        </div>
      )}

      <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '1.25rem', color: '#e2e8f0', marginTop: 0 }}>Historical Snapshots</h2>
        {snapshots && snapshots.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '0.75rem' }}>Date</th>
                <th style={{ padding: '0.75rem' }}>Market Value</th>
                <th style={{ padding: '0.75rem' }}>Mod Dur</th>
                <th style={{ padding: '0.75rem' }}>DV01</th>
                <th style={{ padding: '0.75rem' }}>Hist VaR (95%)</th>
                <th style={{ padding: '0.75rem' }}>Open Breaches</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.map((s: any) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '0.75rem' }}>{s.snapshot_date}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(s.total_market_value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  <td style={{ padding: '0.75rem' }}>{Number(s.weighted_modified_duration).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>${Number(s.total_dv01).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  <td style={{ padding: '0.75rem' }}>{s.historical_var_95_1d !== null ? `$${Number(s.historical_var_95_1d).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : 'N/A'}</td>
                  <td style={{ padding: '0.75rem' }}>{s.open_breach_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: '#94a3b8' }}>No historical snapshots available.</div>
        )}
      </div>
    </div>
  );
};
