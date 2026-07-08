import { useQuery } from '@tanstack/react-query';
import { fetchDataStatus } from '../api/client';

export const DataMonitor = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dataStatus'],
    queryFn: fetchDataStatus,
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#e2e8f0', margin: 0 }}>Data Monitor</h1>
        <button 
          onClick={() => refetch()}
          style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Refresh Data
        </button>
      </div>
      
      {isLoading ? (
        <p style={{ color: '#94a3b8' }}>Loading data status...</p>
      ) : isError ? (
        <p style={{ color: '#ef4444' }}>Error loading data status</p>
      ) : !data || data.length === 0 ? (
        <p style={{ color: '#94a3b8' }}>No data ingestions have been run yet.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {data.map((item: any, idx: number) => (
            <div key={idx} style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#cbd5e1', marginBottom: '1rem' }}>{item.dataset}</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Source:</span> 
                  <span style={{ color: '#e2e8f0' }}>{item.source}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Status:</span> 
                  <span style={{ color: item.last_status === 'SUCCESS' ? '#22c55e' : item.last_status === 'FAILED' ? '#ef4444' : '#eab308' }}>
                    {item.last_status}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Last Successful Update:</span> 
                  <span style={{ color: '#e2e8f0' }}>
                    {item.last_successful_update ? new Date(item.last_successful_update).toLocaleString() : 'Never'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Records Fetched:</span> 
                  <span style={{ color: '#e2e8f0' }}>{item.records_fetched}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Records Inserted:</span> 
                  <span style={{ color: '#e2e8f0' }}>{item.records_inserted}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
