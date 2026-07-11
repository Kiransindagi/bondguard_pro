import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPortfolioRiskReport, evaluatePortfolioRiskControl,
  acknowledgeBreach, getBreachWorkflow, assignBreach,
  reviewBreach, resolveBreach, getAssignableUsers,
} from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td, Btn, StatusBadge, KVRow } from '../components/ui';

const statusVariant = (s: string) => s === 'PASS' ? 'ok' : s === 'WARNING' ? 'warning' : s === 'BREACH' || s === 'FAILED' ? 'danger' : 'muted';

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
};

export const RiskControl = () => {
  const queryClient = useQueryClient();
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: report, isLoading, isError, error } = useQuery({
    queryKey: ['riskReport', portfolioId],
    queryFn: () => getPortfolioRiskReport(portfolioId!),
    enabled: !!portfolioId,
  });

  const evalMutation = useMutation({
    mutationFn: () => evaluatePortfolioRiskControl(portfolioId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] }),
  });

  const ackMutation = useMutation({
    mutationFn: ({ id, note }: { id: number; note: string }) => acknowledgeBreach(id, note),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] }),
  });

  const [ackModal, setAckModal] = useState<{ open: boolean; breachId: number | null; note: string }>({ open: false, breachId: null, note: '' });
  const [selectedBreachId, setSelectedBreachId] = useState<number | null>(null);
  const [workflowNotes, setWorkflowNotes] = useState('');
  const [assignedUserId, setAssignedUserId] = useState<number | null>(null);

  const { data: workflowData } = useQuery({
    queryKey: ['breachWorkflow', selectedBreachId],
    queryFn: () => getBreachWorkflow(selectedBreachId!),
    enabled: selectedBreachId !== null,
  });

  const { data: assignableUsers } = useQuery({ queryKey: ['assignableUsers'], queryFn: getAssignableUsers });

  const assignMutation = useMutation({
    mutationFn: ({ id, userId }: { id: number; userId: number }) => assignBreach(id, userId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] }); queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] }); },
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) => reviewBreach(id, notes),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] }); queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] }); setWorkflowNotes(''); },
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) => resolveBreach(id, notes),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['breachWorkflow', selectedBreachId] }); queryClient.invalidateQueries({ queryKey: ['riskReport', portfolioId] }); setSelectedBreachId(null); setWorkflowNotes(''); },
  });

  if (!portfolioId) return <><PageHeader title="Risk Control Center" description="Portfolio compliance and limit governance" /><EmptyState message="No portfolio selected. Please select a portfolio." /></>;
  if (isLoading) return <LoadingState message="Loading Risk Control Center..." />;
  if (isError) return <ErrorState message={`Error: ${String(error)}`} />;
  if (!report) return <EmptyState message="No risk report available." />;

  const handleAck = () => {
    if (ackModal.breachId) { ackMutation.mutate({ id: ackModal.breachId, note: ackModal.note }); setAckModal({ open: false, breachId: null, note: '' }); }
  };

  return (
    <div>
      <PageHeader
        title="Risk Control Center"
        description={`Portfolio: ${report.portfolio.name}  |  Last evaluation: ${new Date(report.report_metadata.generated_at).toLocaleString()}`}
        badge={{ label: report.report_metadata.overall_status, variant: statusVariant(report.report_metadata.overall_status) as any }}
        action={<Btn variant="primary" size="sm" onClick={() => evalMutation.mutate()} disabled={evalMutation.isPending}>{evalMutation.isPending ? 'Evaluating...' : 'Evaluate Now'}</Btn>}
      />

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '24px' }}>
        <MetricCard label="Limits Evaluated" value={String(report.limit_summary.evaluated_limit_count)} />
        <MetricCard label="Pass" value={String(report.limit_summary.pass_count)} accent />
        <MetricCard label="Warnings" value={String(report.limit_summary.warning_count)} warning={report.limit_summary.warning_count > 0} />
        <MetricCard label="Breaches" value={String(report.limit_summary.breach_count)} danger={report.limit_summary.breach_count > 0} />
        <MetricCard label="Not Evaluated" value={String(report.limit_summary.not_evaluated_count)} />
      </div>

      {/* Model Governance */}
      <DataPanel title="Model Governance & Limitations" style={{ marginBottom: '24px' }}>
        {report.model_governance.degraded_models.length > 0 && (
          <div style={{ color: 'var(--text-warning)', marginBottom: '8px', fontSize: '12px' }}>
            <strong>Degraded Models:</strong> {report.model_governance.degraded_models.join(', ')}
          </div>
        )}
        {report.model_governance.proxy_models.length > 0 && (
          <div style={{ color: 'var(--text-warning)', marginBottom: '8px', fontSize: '12px' }}>
            <strong>Proxy Models:</strong> {report.model_governance.proxy_models.join(', ')}
          </div>
        )}
        <ul style={{ color: 'var(--text-muted)', margin: 0, paddingLeft: '16px', fontSize: '12px' }}>
          {report.model_governance.limitations.map((lim: string, idx: number) => <li key={idx}>{lim}</li>)}
        </ul>
      </DataPanel>

      {/* Active Breaches */}
      <SectionHeader title={`Active Breaches (${report.active_breaches.length})`} />
      {report.active_breaches.length === 0 ? <EmptyState message="No active breaches." /> : (
        <DataPanel noPad style={{ marginBottom: '24px' }}>
          <TablePanel>
            <thead>
              <tr>
                <Th>Limit Code</Th><Th>Severity</Th><Th>Metric</Th>
                <Th right>Observed</Th><Th right>Threshold</Th><Th right>Breach Amt</Th>
                <Th>Status</Th><Th>Action</Th>
              </tr>
            </thead>
            <tbody>
              {report.active_breaches.map((b: any) => (
                <tr key={b.breach_id}>
                  <Td>
                    <button onClick={() => setSelectedBreachId(b.breach_id)} style={{ background: 'none', border: 'none', color: 'var(--text-accent)', cursor: 'pointer', padding: 0, fontWeight: 600, fontSize: '12px', textDecoration: 'underline' }}>
                      {b.limit_code}
                    </button>
                  </Td>
                  <Td><StatusBadge label={b.severity} variant="danger" /></Td>
                  <Td>{b.metric_type}</Td>
                  <Td right mono>{Number(b.observed_value).toFixed(2)}</Td>
                  <Td right mono>{Number(b.threshold_value).toFixed(2)}</Td>
                  <Td right mono>{Number(b.breach_amount).toFixed(2)}</Td>
                  <Td><StatusBadge label={b.status} variant={statusVariant(b.status) as any} /></Td>
                  <Td>
                    {b.status === 'OPEN' && (
                      <Btn variant="secondary" size="sm" onClick={() => setAckModal({ open: true, breachId: b.breach_id, note: '' })}>Acknowledge</Btn>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        </DataPanel>
      )}

      {/* Limit Utilization */}
      <SectionHeader title="Limit Utilization" />
      <DataPanel noPad style={{ marginBottom: '24px' }}>
        <TablePanel>
          <thead>
            <tr><Th>Metric</Th><Th right>Observed</Th><Th right>Threshold</Th><Th right>Util %</Th><Th>Status</Th><Th>Source</Th></tr>
          </thead>
          <tbody>
            {report.limit_results.map((r: any, idx: number) => (
              <tr key={idx}>
                <Td>{r.metric_type}</Td>
                <Td right mono>{r.observed_value !== null ? `${Number(r.observed_value).toFixed(4)} ${r.unit}` : 'N/A'}</Td>
                <Td right mono>{Number(r.threshold_value).toFixed(4)} {r.unit}</Td>
                <Td right mono>{r.utilization_percent !== null ? `${(Number(r.utilization_percent) * 100).toFixed(1)}%` : 'N/A'}</Td>
                <Td><StatusBadge label={r.status} variant={statusVariant(r.status) as any} /></Td>
                <Td>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.calculation_source}</span>
                  {r.limitations && <div style={{ color: 'var(--text-critical)', fontSize: '10px' }}>{r.limitations}</div>}
                </Td>
              </tr>
            ))}
          </tbody>
        </TablePanel>
      </DataPanel>

      {/* Acknowledge Modal */}
      {ackModal.open && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
          <div style={{ backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-muted)', borderRadius: 'var(--radius-lg)', padding: '28px', width: '420px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '16px' }}>Acknowledge Breach</h3>
            <textarea value={ackModal.note} onChange={e => setAckModal({ ...ackModal, note: e.target.value })} placeholder="Acknowledgment note..." style={{ ...inputStyle, height: '80px', marginBottom: '16px', resize: 'vertical' }} />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" size="sm" onClick={() => setAckModal({ open: false, breachId: null, note: '' })}>Cancel</Btn>
              <Btn variant="primary" size="sm" onClick={handleAck} disabled={ackMutation.isPending}>Confirm</Btn>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Side Panel */}
      {selectedBreachId && workflowData && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: '420px', backgroundColor: 'var(--bg-shell)', borderLeft: '1px solid var(--border-muted)', boxShadow: '-16px 0 32px rgba(0,0,0,0.5)', zIndex: 150, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Breach #{workflowData.breach.id}</span>
            <button onClick={() => setSelectedBreachId(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '18px', cursor: 'pointer', lineHeight: 1 }}>&times;</button>
          </div>

          <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <StatusBadge label={workflowData.breach.status} variant={statusVariant(workflowData.breach.status) as any} />
              <StatusBadge label={workflowData.is_overdue ? 'OVERDUE SLA' : 'SLA ACTIVE'} variant={workflowData.is_overdue ? 'danger' : 'ok'} />
            </div>

            <DataPanel>
              <KVRow label="Observed" value={Number(workflowData.breach.observed_value).toFixed(2)} />
              <KVRow label="Threshold" value={Number(workflowData.breach.threshold_value).toFixed(2)} />
              <KVRow label="Breach Amount" value={<span style={{ color: 'var(--text-critical)', fontWeight: 600 }}>{Number(workflowData.breach.breach_amount).toFixed(2)}</span>} />
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Opened: {new Date(workflowData.breach.opened_at).toLocaleString()}
                {workflowData.breach.sla_deadline && ` | SLA: ${new Date(workflowData.breach.sla_deadline).toLocaleString()}`}
              </div>
            </DataPanel>

            {/* Assign */}
            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '6px' }}>Assign</label>
              <div style={{ display: 'flex', gap: '6px' }}>
                <select value={assignedUserId || ''} onChange={e => setAssignedUserId(Number(e.target.value))} style={{ ...inputStyle, flex: 1, fontSize: '11px' }}>
                  <option value="">Select...</option>
                  {assignableUsers?.map((u: any) => <option key={u.id} value={u.id}>{u.username} ({u.roles.join(', ')})</option>)}
                </select>
                <Btn variant="primary" size="sm" onClick={() => assignedUserId && assignMutation.mutate({ id: workflowData.breach.id, userId: assignedUserId })} disabled={!assignedUserId || assignMutation.isPending}>Assign</Btn>
              </div>
              {workflowData.breach.assigned_to && <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Currently: <strong>{workflowData.breach.assigned_to}</strong></div>}
            </div>

            {/* Review / Resolve */}
            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '6px' }}>Notes</label>
              <textarea value={workflowNotes} onChange={e => setWorkflowNotes(e.target.value)} placeholder="Review or resolution notes..." style={{ ...inputStyle, height: '64px', resize: 'vertical', marginBottom: '8px' }} />
              <div style={{ display: 'flex', gap: '6px' }}>
                <Btn variant="secondary" size="sm" style={{ flex: 1 }} onClick={() => reviewMutation.mutate({ id: workflowData.breach.id, notes: workflowNotes })} disabled={reviewMutation.isPending || !workflowNotes}>Under Review</Btn>
                <Btn variant="primary" size="sm" style={{ flex: 1 }} onClick={() => resolveMutation.mutate({ id: workflowData.breach.id, notes: workflowNotes })} disabled={resolveMutation.isPending || !workflowNotes}>Resolve</Btn>
              </div>
            </div>

            {/* Audit timeline */}
            <div>
              <SectionHeader title="Audit Timeline" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                {workflowData.history?.map((h: any) => (
                  <div key={h.id} style={{ borderLeft: '2px solid var(--accent-border)', paddingLeft: '10px', fontSize: '11px' }}>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{h.event_type} - {h.action}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>by {h.actor} at {new Date(h.timestamp).toLocaleString()}</div>
                    {h.new_state?.review_notes && <div style={{ color: 'var(--text-warning)', fontStyle: 'italic', fontSize: '10px' }}>Note: {h.new_state.review_notes}</div>}
                    {h.new_state?.resolution_note && <div style={{ color: 'var(--text-positive)', fontStyle: 'italic', fontSize: '10px' }}>Resolved: {h.new_state.resolution_note}</div>}
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
