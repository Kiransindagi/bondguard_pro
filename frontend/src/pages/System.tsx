import { useQuery } from '@tanstack/react-query';
import { fetchSystemStatus, fetchDatabaseStatus } from '../api/client';

export const System = () => {
  const { data: sysStatus, isLoading: sysLoading, isError: sysError } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: fetchSystemStatus,
  });

  const { data: dbStatus, isLoading: dbLoading, isError: dbError } = useQuery({
    queryKey: ['dbStatus'],
    queryFn: fetchDatabaseStatus,
  });

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e2e8f0' }}>System Status</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
          <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>API Status</h2>
          {sysLoading ? (
            <p style={{ color: '#94a3b8' }}>Loading...</p>
          ) : sysError ? (
            <p style={{ color: '#ef4444' }}>Failed to connect to API</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Status:</span> <span style={{ color: '#22c55e' }}>{sysStatus.status}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Environment:</span> <span style={{ color: '#e2e8f0' }}>{sysStatus.environment}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Version:</span> <span style={{ color: '#e2e8f0' }}>{sysStatus.version}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Last Checked:</span> <span style={{ color: '#e2e8f0' }}>{new Date(sysStatus.timestamp).toLocaleString()}</span></div>
            </div>
          )}
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
          <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>Database Status</h2>
          {dbLoading ? (
            <p style={{ color: '#94a3b8' }}>Loading...</p>
          ) : dbError ? (
            <p style={{ color: '#ef4444' }}>Failed to connect to Database</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Status:</span> <span style={{ color: '#22c55e' }}>{dbStatus.status}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Last Checked:</span> <span style={{ color: '#e2e8f0' }}>{new Date(dbStatus.timestamp).toLocaleString()}</span></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
