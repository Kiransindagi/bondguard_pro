import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRiskLimits, deactivateRiskLimit } from '../api/client';
import type { RiskLimitResponse } from '../api/risk_types';

export const RiskLimits = () => {
  const queryClient = useQueryClient();

  const { data: limits, isLoading, isError, error } = useQuery({
    queryKey: ['riskLimits'],
    queryFn: getRiskLimits
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => deactivateRiskLimit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskLimits'] });
    }
  });

  if (isLoading) return <div style={{ color: '#94a3b8' }}>Loading Limits...</div>;
  if (isError) return <div style={{ color: '#ef4444' }}>Error: {String(error)}</div>;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1rem' }}>Risk Limits Management</h1>
      <p style={{ color: '#94a3b8' }}>Manage global and portfolio-specific risk constraints.</p>
      
      <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '8px', color: '#eab308', marginBottom: '2rem' }}>
        <strong>DEMONSTRATION POLICY LIMIT — NOT A REGULATORY REQUIREMENT</strong>
        <p style={{ margin: 0 }}>These seeded limits are for demonstration purposes only.</p>
      </div>

      <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '0.75rem' }}>Code</th>
              <th style={{ padding: '0.75rem' }}>Name</th>
              <th style={{ padding: '0.75rem' }}>Metric</th>
              <th style={{ padding: '0.75rem' }}>Scope</th>
              <th style={{ padding: '0.75rem' }}>Threshold</th>
              <th style={{ padding: '0.75rem' }}>Direction</th>
              <th style={{ padding: '0.75rem' }}>Status</th>
              <th style={{ padding: '0.75rem' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {limits?.map((lim: RiskLimitResponse) => (
              <tr key={lim.id} style={{ borderBottom: '1px solid #334155', opacity: lim.is_active ? 1 : 0.5 }}>
                <td style={{ padding: '0.75rem' }}>{lim.code}</td>
                <td style={{ padding: '0.75rem' }}>{lim.name}</td>
                <td style={{ padding: '0.75rem' }}>{lim.metric_type}</td>
                <td style={{ padding: '0.75rem' }}>{lim.scope_type} {lim.scope_value}</td>
                <td style={{ padding: '0.75rem' }}>{lim.limit_threshold}</td>
                <td style={{ padding: '0.75rem' }}>{lim.direction}</td>
                <td style={{ padding: '0.75rem' }}>{lim.is_active ? 'Active' : 'Inactive'}</td>
                <td style={{ padding: '0.75rem' }}>
                  {lim.is_active && (
                    <button 
                      onClick={() => deactivateMutation.mutate(lim.id)}
                      disabled={deactivateMutation.isPending}
                      style={{ padding: '0.25rem 0.5rem', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
