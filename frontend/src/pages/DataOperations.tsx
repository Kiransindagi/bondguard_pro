import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPipelineRuns, triggerPipelineRun } from '../api/client';
import { PageHeader, DataPanel, SectionHeader, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td, Btn, StatusBadge } from '../components/ui';

const selectStyle: React.CSSProperties = {
  padding: '7px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '11px',
};

export const DataOperations = () => {
  const queryClient = useQueryClient();
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [runType, setRunType] = useState('INCREMENTAL');

  const { data: runs, isLoading, isError, refetch } = useQuery({ queryKey: ['pipelineRuns'], queryFn: getPipelineRuns });
  const mutation = useMutation({
    mutationFn: (params: any) => triggerPipelineRun(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipelineRuns'] }),
  });

  return (
    <div>
      <PageHeader
        title="Data Operations"
        description="Data ingestion pipeline management and execution history"
        action={
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select value={runType} onChange={e => setRunType(e.target.value)} style={selectStyle}>
              <option value="INCREMENTAL">Incremental</option>
              <option value="BACKFILL">Full Backfill (3 Yrs)</option>
            </select>
            <Btn variant="primary" size="sm" onClick={() => mutation.mutate({ run_type: runType })} disabled={mutation.isPending}>
              {mutation.isPending ? 'Executing...' : 'Trigger Pipeline'}
            </Btn>
            <Btn variant="ghost" size="sm" onClick={() => refetch()}>Refresh</Btn>
          </div>
        }
      />

      {isLoading ? <LoadingState /> : isError ? <ErrorState /> : !runs || runs.length === 0 ? (
        <EmptyState message="No pipeline runs have been executed yet." />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {/* History */}
          <div>
            <SectionHeader title="Ingestion History" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '70vh', overflowY: 'auto' }}>
              {runs.map((run: any) => (
                <DataPanel key={run.id} style={{
                  cursor: 'pointer',
                  borderColor: selectedRun?.id === run.id ? 'var(--accent-border)' : undefined,
                  backgroundColor: selectedRun?.id === run.id ? 'var(--bg-panel-hover)' : undefined,
                }} bodyStyle={{ padding: '14px 18px' }}>
                  <div onClick={() => setSelectedRun(run)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>Run #{run.id} - {run.run_type}</span>
                      <StatusBadge label={run.status} variant={run.status === 'SUCCESS' ? 'ok' : run.status === 'PARTIAL_SUCCESS' ? 'warning' : 'danger'} />
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <span>Triggered: {run.triggered_by}</span>
                      <span>Started: {new Date(run.started_at).toLocaleString()}</span>
                      {run.completed_at && <span>Completed: {new Date(run.completed_at).toLocaleString()}</span>}
                      <span>Jobs: {run.successful_jobs} OK / {run.failed_jobs} Failed ({run.total_jobs} total)</span>
                      {run.error_summary && <span style={{ color: 'var(--text-critical)' }}>{run.error_summary}</span>}
                    </div>
                  </div>
                </DataPanel>
              ))}
            </div>
          </div>

          {/* Details */}
          <div>
            <SectionHeader title="Job Details" />
            {!selectedRun ? (
              <DataPanel style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <EmptyState message="Select a run to view job results." />
              </DataPanel>
            ) : (
              <DataPanel title={`Run #${selectedRun.id} Results`} noPad>
                {!selectedRun.job_runs || selectedRun.job_runs.length === 0 ? <EmptyState message="No job details." /> : (
                  <TablePanel>
                    <thead><tr><Th>Dataset</Th><Th>Status</Th><Th right>Fetched</Th><Th right>Inserted</Th><Th>Error</Th></tr></thead>
                    <tbody>
                      {selectedRun.job_runs.map((job: any) => (
                        <tr key={job.id}>
                          <Td style={{ fontWeight: 500 }}>{job.dataset_key}</Td>
                          <Td><StatusBadge label={job.status} variant={job.status === 'SUCCESS' ? 'ok' : 'danger'} /></Td>
                          <Td right mono>{job.rows_fetched}</Td>
                          <Td right mono>{job.rows_inserted}</Td>
                          <Td style={{ color: 'var(--text-critical)', fontSize: '11px', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{job.error_message || '-'}</Td>
                        </tr>
                      ))}
                    </tbody>
                  </TablePanel>
                )}
              </DataPanel>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default DataOperations;
