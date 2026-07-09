import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLatestQualitySummary, getDatasetQualityStatus, getDatasetQualityDetails, triggerDataQualityRun } from '../api/client';

export const DataQuality = () => {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);

  // Latest summary run
  const { data: summary, refetch: refetchSummary } = useQuery({
    queryKey: ['qualitySummary'],
    queryFn: getLatestQualitySummary,
  });

  // Dataset list
  const { data: datasets, isLoading: isDatasetsLoading, isError, refetch: refetchDatasets } = useQuery({
    queryKey: ['datasetsQualityStatus'],
    queryFn: getDatasetQualityStatus,
  });

  // Details for selected dataset
  const { data: details, isLoading: isDetailsLoading } = useQuery({
    queryKey: ['datasetQualityDetails', selectedDataset],
    queryFn: () => (selectedDataset ? getDatasetQualityDetails(selectedDataset) : Promise.resolve([])),
    enabled: !!selectedDataset,
  });

  const mutation = useMutation({
    mutationFn: triggerDataQualityRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qualitySummary'] });
      queryClient.invalidateQueries({ queryKey: ['datasetsQualityStatus'] });
      if (selectedDataset) {
        queryClient.invalidateQueries({ queryKey: ['datasetQualityDetails', selectedDataset] });
      }
    },
  });

  const handleRunChecks = () => {
    mutation.mutate();
  };

  const handleRefresh = () => {
    refetchSummary();
    refetchDatasets();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Data Quality</h1>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            onClick={handleRunChecks}
            disabled={mutation.isPending}
            style={{ 
              padding: '0.5rem 1rem', 
              backgroundColor: '#10b981', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: mutation.isPending ? 'not-allowed' : 'pointer',
              opacity: mutation.isPending ? 0.6 : 1
            }}
          >
            {mutation.isPending ? 'Running Checks...' : 'Run Quality Checks'}
          </button>
          <button 
            onClick={handleRefresh}
            style={{ padding: '0.5rem 1rem', backgroundColor: '#475569', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Status Panel */}
      {summary && (
        <div style={{ 
          padding: '1.25rem', 
          backgroundColor: '#1e293b', 
          borderRadius: '8px', 
          borderLeft: `5px solid ${summary.status === 'PASS' ? '#10b981' : summary.status === 'WARNING' ? '#f59e0b' : '#ef4444'}`,
          borderTop: '1px solid #334155',
          borderRight: '1px solid #334155',
          borderBottom: '1px solid #334155',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Latest Audit Quality Status</div>
            <div style={{ 
              fontSize: '2rem', 
              fontWeight: 'bold', 
              color: summary.status === 'PASS' ? '#10b981' : summary.status === 'WARNING' ? '#f59e0b' : '#ef4444',
              marginTop: '0.25rem' 
            }}>
              {summary.status}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.5rem' }}>
              Checked on: {new Date(summary.started_at).toLocaleString()} | Checked: {summary.datasets_checked} series
            </div>
          </div>
          <div style={{ display: 'flex', gap: '2rem', textAlign: 'right' }}>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#10b981' }}>{summary.checks_passed}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Passed</div>
            </div>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#f59e0b' }}>{summary.checks_warned}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Warnings</div>
            </div>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#ef4444' }}>{summary.checks_failed}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Failures</div>
            </div>
          </div>
        </div>
      )}

      {isDatasetsLoading ? (
        <p style={{ color: '#94a3b8' }}>Loading quality status...</p>
      ) : isError ? (
        <p style={{ color: '#ef4444' }}>Error loading data quality status</p>
      ) : !datasets || datasets.length === 0 ? (
        <p style={{ color: '#94a3b8' }}>No dataset quality metrics available.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          
          {/* Datasets Cards Grid */}
          <div>
            <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Data Series Status</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {datasets.map((ds: any) => {
                const isSelected = selectedDataset === ds.dataset_key;
                return (
                  <div 
                    key={ds.dataset_key}
                    onClick={() => setSelectedDataset(ds.dataset_key)}
                    style={{ 
                      padding: '1rem', 
                      backgroundColor: isSelected ? '#334155' : '#1e293b',
                      borderRadius: '8px',
                      border: '1px solid #334155',
                      cursor: 'pointer',
                      transition: 'transform 0.2s, background-color 0.2s',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    <div style={{ 
                      width: '4px', 
                      height: '100%', 
                      position: 'absolute', 
                      left: 0, 
                      top: 0, 
                      backgroundColor: ds.status === 'PASS' ? '#10b981' : ds.status === 'WARNING' ? '#f59e0b' : ds.status === 'FAIL' ? '#ef4444' : '#475569' 
                    }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 'bold', color: '#f1f5f9', marginLeft: '0.25rem' }}>{ds.dataset_key}</span>
                      <span style={{ 
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        color: ds.status === 'PASS' ? '#10b981' : ds.status === 'WARNING' ? '#f59e0b' : ds.status === 'FAIL' ? '#ef4444' : '#94a3b8'
                      }}>
                        {ds.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.2rem', marginLeft: '0.25rem' }}>
                      <span>Source: {ds.source} | Category: {ds.category}</span>
                      {ds.latest_check_date && (
                        <span>Last Audited: {new Date(ds.latest_check_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Dataset Check Details */}
          <div>
            <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Check Auditing Reports</h2>
            {!selectedDataset ? (
              <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#0f172a', border: '1px dashed #334155', borderRadius: '8px' }}>
                <p style={{ color: '#64748b' }}>Select a data series on the left to review individual test results.</p>
              </div>
            ) : (
              <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ margin: 0, color: '#38bdf8' }}>{selectedDataset} Diagnostic Audit</h3>
                  <button 
                    onClick={() => setSelectedDataset(null)}
                    style={{ fontSize: '0.8rem', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    Clear Selection
                  </button>
                </div>

                {isDetailsLoading ? (
                  <p style={{ color: '#94a3b8' }}>Loading checks...</p>
                ) : !details || details.length === 0 ? (
                  <p style={{ color: '#94a3b8' }}>No diagnostics run yet for this dataset.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {details.map((check: any) => (
                      <div key={check.id} style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#0f172a', 
                        borderRadius: '6px', 
                        border: '1px solid #1e293b'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <span style={{ fontWeight: 'bold', color: '#cbd5e1', textTransform: 'capitalize' }}>
                            {check.check_name.replace('_', ' ')}
                          </span>
                          <span style={{ 
                            fontSize: '0.8rem',
                            fontWeight: 'bold',
                            color: check.status === 'PASS' ? '#10b981' : check.status === 'WARNING' ? '#f59e0b' : '#ef4444'
                          }}>
                            {check.status}
                          </span>
                        </div>
                        <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#94a3b8' }}>{check.message}</p>
                        {check.observed_value !== null && (
                          <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '1rem' }}>
                            <span>Observed: {check.observed_value.toFixed(4)}</span>
                            {check.expected_value !== null && <span>Limit/Expected: {check.expected_value}</span>}
                          </div>
                        )}
                      </div>
                    ))}
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
export default DataQuality;
