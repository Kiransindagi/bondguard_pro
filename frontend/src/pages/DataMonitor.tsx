import { useQuery } from '@tanstack/react-query';
import { fetchDataStatus } from '../api/client';
import { PageHeader, DataPanel, LoadingState, ErrorState, EmptyState, KVRow, StatusBadge, Btn } from '../components/ui';

export const DataMonitor = () => {
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['dataStatus'], queryFn: fetchDataStatus });

  return (
    <div>
      <PageHeader
        title="Data Monitor"
        description="Ingestion pipeline status and data freshness"
        action={<Btn variant="secondary" size="sm" onClick={() => refetch()}>Refresh Data</Btn>}
      />

      {isLoading ? <LoadingState message="Loading data status..." /> : isError ? <ErrorState message="Error loading data status" /> : !data || data.length === 0 ? (
        <EmptyState message="No data ingestions have been run yet." />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
          {data.map((item: any, idx: number) => (
            <DataPanel key={idx} title={item.dataset}>
              <KVRow label="Source" value={item.source} />
              <KVRow label="Status" value={
                <StatusBadge
                  label={item.last_status}
                  variant={item.last_status === 'SUCCESS' ? 'ok' : item.last_status === 'FAILED' ? 'danger' : 'warning'}
                />
              } />
              <KVRow label="Last Successful Update" value={item.last_successful_update ? new Date(item.last_successful_update).toLocaleString() : 'Never'} />
              <KVRow label="Records Fetched" value={item.records_fetched} />
              <KVRow label="Records Inserted" value={item.records_inserted} />
            </DataPanel>
          ))}
        </div>
      )}
    </div>
  );
};
