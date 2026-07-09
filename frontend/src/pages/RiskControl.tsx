import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPortfolioRiskReport,
  evaluatePortfolioRiskControl,
  acknowledgeBreach,
  getBreachWorkflow,
  assignBreach,
  reviewBreach,
  resolveBreach,
  getAssignableUsers
} from '../api/client';

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

  const [selectedBreachId, setSelectedBreachId] = useState<number | null>(null);
  const [workflowNotes, setWorkflowNotes] = useState('');
  const [assignedUserId, setAssignedUserId] = useState<number | null>(null);

  const { data: workflowData } = useQuery({
    queryKey: ['breachWorkflow', selectedBreachId],
    queryFn: () => getBreachWorkflow(selectedBreachId!),
    enabled: selectedBreachId !== null
  });

  const { data: assignableUsers } = useQuery({
    queryKey: ['assignableUsers'],
    queryFn: getAssignableUsers
  });

  const assignMutation = useMutation({
    mutationFn: ({ id, userId }: { id: number, userId: number }) => assignBreach(id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] });
      queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] });
    }
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number, notes: string }) => reviewBreach(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] });
      queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] });
      setWorkflowNotes('');
    }
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number, notes: string }) => resolveBreach(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] });
      queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] });
      setSelectedBreachId(null);
      setWorkflowNotes('');
    }
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
                  <td style={{ padding: '0.75rem' }}>
                    <button
                      onClick={() => setSelectedBreachId(b.breach_id)}
                      style={{ background: 'transparent', border: 'none', color: '#38bdf8', textDecoration: 'underline', cursor: 'pointer', padding: 0, fontWeight: 'bold' }}
                    >
                      {b.limit_code}
                    </button>
                  </td>
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

      {selectedBreachId && workflowData && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: '450px', backgroundColor: '#1e293b', borderLeft: '1px solid #334155', boxShadow: '-10px 0 15px -3px rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', flexDirection: 'column', padding: '1.5rem', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
            <h3 style={{ margin: 0, color: '#e2e8f0' }}>Workflow Detail: Breach {workflowData.breach.id}</h3>
            <button onClick={() => setSelectedBreachId(null)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.25rem', cursor: 'pointer' }}>&times;</button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Status: 
                <strong style={{ marginLeft: '0.25rem', color: statusColor(workflowData.breach.status) }}>{workflowData.breach.status}</strong>
              </span>
              {workflowData.is_overdue ? (
                <span style={{ backgroundColor: '#ef444433', color: '#ef4444', fontSize: '0.75rem', fontWeight: 'bold', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>OVERDUE SLA</span>
              ) : (
                <span style={{ backgroundColor: '#22c55e33', color: '#22c55e', fontSize: '0.75rem', fontWeight: 'bold', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>SLA ACTIVE</span>
              )}
            </div>

            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '6px', fontSize: '0.875rem', border: '1px solid #334155' }}>
              <div style={{ marginBottom: '0.5rem' }}>Observed: <strong>{Number(workflowData.breach.observed_value).toFixed(2)}</strong> vs Threshold: <strong>{Number(workflowData.breach.threshold_value).toFixed(2)}</strong></div>
              <div>Breach Amount: <strong style={{ color: '#ef4444' }}>{Number(workflowData.breach.breach_amount).toFixed(2)}</strong></div>
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}>
                Opened: {new Date(workflowData.breach.opened_at).toLocaleString()}
                {workflowData.breach.sla_deadline && ` • SLA Deadline: ${new Date(workflowData.breach.sla_deadline).toLocaleString()}`}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Assign Action:</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select 
                  value={assignedUserId || ''} 
                  onChange={e => setAssignedUserId(Number(e.target.value))}
                  style={{ flex: 1, padding: '0.5rem', backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '4px', color: 'white' }}
                >
                  <option value="">Select Assignee...</option>
                  {assignableUsers?.map((u: any) => (
                    <option key={u.id} value={u.id}>{u.username} ({u.roles.join(', ')})</option>
                  ))}
                </select>
                <button 
                  onClick={() => assignedUserId && assignMutation.mutate({ id: workflowData.breach.id, userId: assignedUserId })}
                  disabled={!assignedUserId || assignMutation.isPending}
                  style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Assign
                </button>
              </div>
              {workflowData.breach.assigned_to && (
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>Currently assigned to: <strong>{workflowData.breach.assigned_to}</strong></div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Review / Resolution Notes:</label>
              <textarea 
                value={workflowNotes}
                onChange={e => setWorkflowNotes(e.target.value)}
                placeholder="Type review updates or resolution summary here..."
                style={{ width: '100%', height: '80px', padding: '0.5rem', borderRadius: '4px', backgroundColor: '#0f172a', color: 'white', border: '1px solid #334155', marginBottom: '0.5rem' }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => reviewMutation.mutate({ id: workflowData.breach.id, notes: workflowNotes })}
                  disabled={reviewMutation.isPending || !workflowNotes}
                  style={{ flex: 1, padding: '0.5rem', backgroundColor: '#eab308', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Mark Under Review
                </button>
                <button
                  onClick={() => resolveMutation.mutate({ id: workflowData.breach.id, notes: workflowNotes })}
                  disabled={resolveMutation.isPending || !workflowNotes}
                  style={{ flex: 1, padding: '0.5rem', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Resolve Breach
                </button>
              </div>
            </div>

            <div>
              <h4 style={{ color: '#e2e8f0', borderBottom: '1px solid #334155', paddingBottom: '0.25rem', marginBottom: '0.5rem' }}>Audit Timeline</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.50rem', maxHeight: '180px', overflowY: 'auto', paddingRight: '0.25rem' }}>
                {workflowData.history?.map((h: any) => (
                  <div key={h.id} style={{ fontSize: '0.75rem', borderLeft: '2px solid #3b82f6', paddingLeft: '0.5rem', margin: '0.25rem 0' }}>
                    <div style={{ color: '#cbd5e1', fontWeight: 'semibold' }}>{h.event_type} - {h.action}</div>
                    <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>by {h.actor} at {new Date(h.timestamp).toLocaleString()}</div>
                    {h.new_state?.review_notes && <div style={{ color: '#eab308', fontStyle: 'italic' }}>Note: {h.new_state.review_notes}</div>}
                    {h.new_state?.resolution_note && <div style={{ color: '#10b981', fontStyle: 'italic' }}>Resolved: {h.new_state.resolution_note}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
