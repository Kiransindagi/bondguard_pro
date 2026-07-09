import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPipelineRuns, triggerPipelineRun } from '../api/client';

export const DataOperations = () => {
  const queryClient = useQueryClient();
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [runType, setRunType] = useState<string>('INCREMENTAL');

  const { data: runs, isLoading, isError, refetch } = useQuery({
    queryKey: ['pipelineRuns'],
    queryFn: getPipelineRuns,
  });

  const mutation = useMutation({
    mutationFn: (params: any) => triggerPipelineRun(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelineRuns'] });
    },
  });

  const handleRun = () => {
    mutation.mutate({ run_type: runType });
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Data Operations</h1>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select 
            value={runType} 
            onChange={(e) => setRunType(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: '#1e293b', 
              color: '#cbd5e1', 
              border: '1px solid #334155', 
              borderRadius: '4px',
              cursor: 'pointer' 
            }}
          >
            <option value="INCREMENTAL">Incremental Ingestion</option>
            <option value="BACKFILL">Full Backfill (3 Yrs)</option>
          </select>
          <button 
            onClick={handleRun}
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
            {mutation.isPending ? 'Executing...' : 'Trigger Pipeline'}
          </button>
          <button 
            onClick={() => refetch()}
            style={{ padding: '0.5rem 1rem', backgroundColor: '#475569', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Refresh
          </button>
        </div>
      </div>

      {isLoading ? (
        <p style={{ color: '#94a3b8' }}>Loading pipeline history...</p>
      ) : isError ? (
        <p style={{ color: '#ef4444' }}>Error loading pipeline history</p>
      ) : !runs || runs.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
          <p style={{ color: '#94a3b8' }}>No pipeline runs have been executed yet.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* Runs History List */}
          <div>
            <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Ingestion History</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '70vh', overflowY: 'auto' }}>
              {runs.map((run: any) => {
                const isSelected = selectedRun?.id === run.id;
                return (
                  <div 
                    key={run.id} 
                    onClick={() => setSelectedRun(run)}
                    style={{ 
                      padding: '1rem', 
                      backgroundColor: isSelected ? '#334155' : '#1e293b', 
                      borderRadius: '8px', 
                      border: '1px solid #334155',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 'bold', color: '#f1f5f9' }}>Run #{run.id} - {run.run_type}</span>
                      <span style={{ 
                        color: run.status === 'SUCCESS' ? '#22c55e' : run.status === 'PARTIAL_SUCCESS' ? '#eab308' : '#ef4444',
                        fontWeight: 'bold'
                      }}>
                        {run.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span>Triggered: {run.triggered_by}</span>
                      <span>Started: {new Date(run.started_at).toLocaleString()}</span>
                      {run.completed_at && <span>Completed: {new Date(run.completed_at).toLocaleString()}</span>}
                      <span>Jobs: {run.successful_jobs} Succeeded / {run.failed_jobs} Failed ({run.total_jobs} Total)</span>
                      {run.error_summary && (
                        <span style={{ color: '#f87171', marginTop: '0.25rem' }}>Error: {run.error_summary}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Run Details */}
          <div>
            <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Job Details</h2>
            {!selectedRun ? (
              <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#0f172a', border: '1px dashed #334155', borderRadius: '8px' }}>
                <p style={{ color: '#64748b' }}>Select an ingestion run from the history to view detailed job results.</p>
              </div>
            ) : (
              <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 1rem 0', color: '#38bdf8' }}>Run #{selectedRun.id} Detailed Results</h3>
                
                {!selectedRun.job_runs || selectedRun.job_runs.length === 0 ? (
                  <p style={{ color: '#94a3b8' }}>No job details available for this run.</p>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', color: '#cbd5e1' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                          <th style={{ padding: '0.5rem' }}>Dataset</th>
                          <th style={{ padding: '0.5rem' }}>Status</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right' }}>Fetched</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right' }}>Inserted</th>
                          <th style={{ padding: '0.5rem' }}>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedRun.job_runs.map((job: any) => (
                          <tr key={job.id} style={{ borderBottom: '1px solid #1e293b' }}>
                            <td style={{ padding: '0.5rem', fontWeight: '500' }}>{job.dataset_key}</td>
                            <td style={{ 
                              padding: '0.5rem', 
                              color: job.status === 'SUCCESS' ? '#22c55e' : '#ef4444',
                              fontWeight: '500'
                            }}>
                              {job.status}
                            </td>
                            <td style={{ padding: '0.5rem', textAlign: 'right' }}>{job.rows_fetched}</td>
                            <td style={{ padding: '0.5rem', textAlign: 'right' }}>{job.rows_inserted}</td>
                            <td style={{ padding: '0.5rem', color: '#f87171', fontSize: '0.8rem', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {job.error_message || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default DataOperations;
