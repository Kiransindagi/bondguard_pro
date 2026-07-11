import { useQuery } from '@tanstack/react-query';
import { fetchSystemStatus, fetchDatabaseStatus } from '../api/client';
import { PageHeader, DataPanel, LoadingState, ErrorState, KVRow, StatusBadge } from '../components/ui';

export const System = () => {
  const { data: sysStatus, isLoading: sysLoading, isError: sysError } = useQuery({ queryKey: ['systemStatus'], queryFn: fetchSystemStatus });
  const { data: dbStatus, isLoading: dbLoading, isError: dbError } = useQuery({ queryKey: ['dbStatus'], queryFn: fetchDatabaseStatus });

  return (
    <div>
      <PageHeader title="System" description="Platform health and connectivity" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <DataPanel title="API Status">
          {sysLoading ? <LoadingState /> : sysError ? <ErrorState message="Failed to connect to API" /> : (
            <>
              <KVRow label="Status" value={<StatusBadge label={sysStatus.status} variant="ok" />} />
              <KVRow label="Environment" value={sysStatus.environment} />
              <KVRow label="Version" value={sysStatus.version} />
              <KVRow label="Last Checked" value={new Date(sysStatus.timestamp).toLocaleString()} />
            </>
          )}
        </DataPanel>
        <DataPanel title="Database Status">
          {dbLoading ? <LoadingState /> : dbError ? <ErrorState message="Failed to connect to Database" /> : (
            <>
              <KVRow label="Status" value={<StatusBadge label={dbStatus.status} variant="ok" />} />
              <KVRow label="Last Checked" value={new Date(dbStatus.timestamp).toLocaleString()} />
            </>
          )}
        </DataPanel>
      </div>
    </div>
  );
};
