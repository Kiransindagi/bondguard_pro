import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLatestQualitySummary, getDatasetQualityStatus, getDatasetQualityDetails, triggerDataQualityRun } from '../api/client';
import { PageHeader, DataPanel, SectionHeader, LoadingState, ErrorState, EmptyState, Btn, StatusBadge } from '../components/ui';

export const DataQuality = () => {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);

  const { data: summary, refetch: refetchSummary } = useQuery({ queryKey: ['qualitySummary'], queryFn: getLatestQualitySummary });
  const { data: datasets, isLoading: isDatasetsLoading, isError, refetch: refetchDatasets } = useQuery({ queryKey: ['datasetsQualityStatus'], queryFn: getDatasetQualityStatus });
  const { data: details, isLoading: isDetailsLoading } = useQuery({
    queryKey: ['datasetQualityDetails', selectedDataset],
    queryFn: () => (selectedDataset ? getDatasetQualityDetails(selectedDataset) : Promise.resolve([])),
    enabled: !!selectedDataset,
  });

  const mutation = useMutation({
    mutationFn: triggerDataQualityRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qualitySummary'] }); queryClient.invalidateQueries({ queryKey: ['datasetsQualityStatus'] });
      if (selectedDataset) queryClient.invalidateQueries({ queryKey: ['datasetQualityDetails', selectedDataset] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Data Quality"
        description="Dataset integrity audits and anomaly detection"
        action={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn variant="primary" size="sm" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? 'Running Checks...' : 'Run Quality Checks'}
            </Btn>
            <Btn variant="ghost" size="sm" onClick={() => { refetchSummary(); refetchDatasets(); }}>Refresh</Btn>
          </div>
        }
      />

      {/* Summary */}
      {summary && (
        <div style={{
          padding: '20px', backgroundColor: 'var(--bg-panel)', borderRadius: 'var(--radius-lg)',
          borderTop: '1px solid var(--border-muted)', borderRight: '1px solid var(--border-muted)', borderBottom: '1px solid var(--border-muted)',
          borderLeft: `4px solid ${summary.status === 'PASS' ? 'var(--text-positive)' : summary.status === 'WARNING' ? 'var(--text-warning)' : 'var(--text-critical)'}`,
          marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Audit Status</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: summary.status === 'PASS' ? 'var(--text-positive)' : summary.status === 'WARNING' ? 'var(--text-warning)' : 'var(--text-critical)', marginTop: '4px' }}>
              {summary.status}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Checked on: {new Date(summary.started_at).toLocaleString()} | Datasets: {summary.datasets_checked}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '32px', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-positive)' }}>{summary.checks_passed}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Passed</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-warning)' }}>{summary.checks_warned}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Warnings</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-critical)' }}>{summary.checks_failed}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Failures</div>
            </div>
          </div>
        </div>
      )}

      {isDatasetsLoading ? <LoadingState /> : isError ? <ErrorState /> : !datasets || datasets.length === 0 ? <EmptyState message="No datasets available." /> : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          
          {/* Datasets */}
          <div>
            <SectionHeader title="Data Series Status" />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              {datasets.map((ds: any) => (
                <DataPanel key={ds.dataset_key} style={{
                  cursor: 'pointer',
                  borderColor: selectedDataset === ds.dataset_key ? 'var(--accent-border)' : undefined,
                  backgroundColor: selectedDataset === ds.dataset_key ? 'var(--bg-panel-hover)' : undefined,
                }} bodyStyle={{ padding: '14px' }}>
                  <div onClick={() => setSelectedDataset(ds.dataset_key)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{ds.dataset_key}</span>
                      <StatusBadge label={ds.status} variant={ds.status === 'PASS' ? 'ok' : ds.status === 'WARNING' ? 'warning' : 'danger'} />
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span>Source: {ds.source} | Cat: {ds.category}</span>
                      {ds.latest_check_date && <span>Audited: {new Date(ds.latest_check_date).toLocaleDateString()}</span>}
                    </div>
                  </div>
                </DataPanel>
              ))}
            </div>
          </div>

          {/* Details */}
          <div>
            <SectionHeader title="Check Auditing Reports" />
            {!selectedDataset ? (
              <DataPanel style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <EmptyState message="Select a data series to review diagnostic results." />
              </DataPanel>
            ) : (
              <DataPanel title={`${selectedDataset} Diagnostics`} headerAction={<Btn variant="ghost" size="sm" onClick={() => setSelectedDataset(null)}>Clear</Btn>} bodyStyle={{ padding: '16px' }}>
                {isDetailsLoading ? <LoadingState /> : !details || details.length === 0 ? <EmptyState message="No diagnostics run for this dataset." /> : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {details.map((check: any) => (
                      <div key={check.id} style={{ padding: '12px', backgroundColor: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{check.check_name.replace(/_/g, ' ')}</span>
                          <StatusBadge label={check.status} variant={check.status === 'PASS' ? 'ok' : check.status === 'WARNING' ? 'warning' : 'danger'} />
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px' }}>{check.message}</div>
                        {check.observed_value !== null && (
                          <div style={{ display: 'flex', gap: '16px', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            <span>Obs: {check.observed_value.toFixed(4)}</span>
                            {check.expected_value !== null && <span>Exp: {check.expected_value}</span>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </DataPanel>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default DataQuality;
