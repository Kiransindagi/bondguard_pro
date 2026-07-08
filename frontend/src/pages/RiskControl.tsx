import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPortfolioRiskReport, evaluatePortfolioRiskControl, acknowledgeBreach } from '../api/client';

export const RiskControl = () => {
  const queryClient = useQueryClient();
  const portfolioId = 1; // standard demo portfolio

  const { data: report, isLoading, isError, error } = useQuery({
    queryKey: ['riskReport', portfolioId],
    queryFn: () => getPortfolioRiskReport(portfolioId)
  });

  const evalMutation = useMutation({
    mutationFn: () => evaluatePortfolioRiskControl(portfolioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] });
    }
  });

  const ackMutation = useMutation({
    mutationFn: ({ id, note }: { id: number, note: string }) => acknowledgeBreach(id, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] });
    }
  });

  const [ackModal, setAckModal] = useState<{ open: boolean, breachId: number | null, note: string }>({
    open: false, breachId: null, note: ''
  });

  if (isLoading) return <div style={{ color: '#94a3b8' }}>Loading Risk Control Center...</div>;
  if (isError) return <div style={{ color: '#ef4444' }}>Error loading risk report: {String(error)}</div>;
  if (!report) return <div style={{ color: '#94a3b8' }}>No risk report available.</div>;

  const handleAck = () => {
    if (ackModal.breachId) {
      ackMutation.mutate({ id: ackModal.breachId, note: ackModal.note });
      setAckModal({ open: false, breachId: null, note: '' });
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'PASS': return '#22c55e';
      case 'WARNING': return '#eab308';
      case 'BREACH': return '#ef4444';
      case 'FAILED': return '#dc2626';
      default: return '#94a3b8';
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1rem' }}>Institutional Risk Control Center</h1>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ margin: 0, color: '#e2e8f0' }}>Portfolio: {report.portfolio.name}</h2>
          <p style={{ margin: 0, color: '#94a3b8' }}>Last Evaluation: {new Date(report.report_metadata.generated_at).toLocaleString()}</p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
            <span style={{ fontWeight: 'bold', color: statusColor(report.report_metadata.overall_status) }}>
              STATUS: {report.report_metadata.overall_status}
            </span>
          </div>
        </div>
        <div>
          <button 
            onClick={() => evalMutation.mutate()} 
            disabled={evalMutation.isPending}
            style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            {evalMutation.isPending ? 'Evaluating...' : 'Evaluate Now'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>Limits Evaluated</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{report.limit_summary.evaluated_limit_count}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#22c55e' }}>Pass</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{report.limit_summary.pass_count}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#eab308' }}>Warnings</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{report.limit_summary.warning_count}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#ef4444' }}>Breaches</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{report.limit_summary.breach_count}</div>
        </div>
        <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
          <div style={{ color: '#94a3b8' }}>Not Evaluated</div>
          <div style={{ fontSize: '1.5rem', color: '#e2e8f0' }}>{report.limit_summary.not_evaluated_count}</div>
        </div>
      </div>

      {/* Model Governance */}
      <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Model Governance & Limitations</h3>
        {report.model_governance.degraded_models.length > 0 && (
          <div style={{ color: '#eab308', marginBottom: '0.5rem' }}>
            <strong>Degraded Models:</strong> {report.model_governance.degraded_models.join(', ')}
          </div>
        )}
        {report.model_governance.proxy_models.length > 0 && (
          <div style={{ color: '#eab308', marginBottom: '0.5rem' }}>
            <strong>Proxy Models:</strong> {report.model_governance.proxy_models.join(', ')}
          </div>
        )}
        <ul style={{ color: '#94a3b8', margin: 0, paddingLeft: '1.5rem' }}>
          {report.model_governance.limitations.map((lim: string, idx: number) => (
            <li key={idx}>{lim}</li>
          ))}
        </ul>
      </div>

      {/* Active Breaches Panel */}
      <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Active Breaches ({report.active_breaches.length})</h3>
      {report.active_breaches.length === 0 ? (
        <p style={{ color: '#94a3b8' }}>No active breaches.</p>
      ) : (
        <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem', marginBottom: '2rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '0.75rem' }}>Limit Code</th>
                <th style={{ padding: '0.75rem' }}>Severity</th>
                <th style={{ padding: '0.75rem' }}>Metric</th>
                <th style={{ padding: '0.75rem' }}>Observed</th>
                <th style={{ padding: '0.75rem' }}>Threshold</th>
                <th style={{ padding: '0.75rem' }}>Breach Amount</th>
                <th style={{ padding: '0.75rem' }}>Status</th>
                <th style={{ padding: '0.75rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {report.active_breaches.map((b: any) => (
                <tr key={b.breach_id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '0.75rem' }}>{b.limit_code}</td>
                  <td style={{ padding: '0.75rem', color: statusColor('BREACH') }}>{b.severity}</td>
                  <td style={{ padding: '0.75rem' }}>{b.metric_type}</td>
                  <td style={{ padding: '0.75rem' }}>{Number(b.observed_value).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>{Number(b.threshold_value).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>{Number(b.breach_amount).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>{b.status}</td>
                  <td style={{ padding: '0.75rem' }}>
                    {b.status === 'OPEN' && (
                      <button 
                        onClick={() => setAckModal({ open: true, breachId: b.breach_id, note: '' })}
                        style={{ padding: '0.25rem 0.5rem', backgroundColor: '#eab308', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Limit Utilization */}
      <h3 style={{ color: '#e2e8f0', marginBottom: '1rem' }}>Limit Utilization</h3>
      <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem', marginBottom: '2rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '0.75rem' }}>Metric</th>
              <th style={{ padding: '0.75rem' }}>Observed Value</th>
              <th style={{ padding: '0.75rem' }}>Threshold</th>
              <th style={{ padding: '0.75rem' }}>Util %</th>
              <th style={{ padding: '0.75rem' }}>Status</th>
              <th style={{ padding: '0.75rem' }}>Source</th>
            </tr>
          </thead>
          <tbody>
            {report.limit_results.map((r: any, idx: number) => (
              <tr key={idx} style={{ borderBottom: '1px solid #334155' }}>
                <td style={{ padding: '0.75rem' }}>{r.metric_type}</td>
                <td style={{ padding: '0.75rem' }}>
                  {r.observed_value !== null ? Number(r.observed_value).toFixed(4) + ' ' + r.unit : 'N/A'}
                </td>
                <td style={{ padding: '0.75rem' }}>{Number(r.threshold_value).toFixed(4)} {r.unit}</td>
                <td style={{ padding: '0.75rem' }}>
                  {r.utilization_percent !== null ? (Number(r.utilization_percent) * 100).toFixed(1) + '%' : 'N/A'}
                </td>
                <td style={{ padding: '0.75rem', color: statusColor(r.status), fontWeight: 'bold' }}>{r.status}</td>
                <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                  {r.calculation_source}
                  {r.limitations && <div style={{ color: '#ef4444' }}>{r.limitations}</div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {ackModal.open && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '8px', width: '400px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Acknowledge Breach</h3>
            <textarea 
              value={ackModal.note} 
              onChange={e => setAckModal({...ackModal, note: e.target.value})}
              placeholder="Acknowledgment note..."
              style={{ width: '100%', height: '100px', marginBottom: '1rem', padding: '0.5rem', borderRadius: '4px', backgroundColor: '#0f172a', color: '#e2e8f0', border: '1px solid #334155' }}
            />
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setAckModal({ open: false, breachId: null, note: '' })} style={{ padding: '0.5rem 1rem', background: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer' }}>Cancel</button>
              <button onClick={handleAck} disabled={ackMutation.isPending} style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Confirm</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
