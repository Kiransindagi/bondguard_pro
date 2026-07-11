import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRiskLimits, deactivateRiskLimit } from '../api/client';
import type { RiskLimitResponse } from '../api/risk_types';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, DataPanel, ModelStatusBanner, LoadingState, ErrorState, TablePanel, Th, Td, Btn, StatusBadge, EmptyState } from '../components/ui';

export const RiskLimits = () => {
  const queryClient = useQueryClient();
  const { selectedPortfolioId: portfolioId } = usePortfolio();
  const { data: limits, isLoading, isError, error } = useQuery({ queryKey: ['riskLimits'], queryFn: getRiskLimits });
  const deactivateMutation = useMutation({
    mutationFn: (id: number) => deactivateRiskLimit(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['riskLimits'] }),
  });

  if (!portfolioId) return <><PageHeader title="Risk Limits" description="Global and portfolio-specific risk constraints" /><EmptyState message="No portfolio selected." /></>;
  if (isLoading) return <LoadingState message="Loading Limits..." />;
  if (isError) return <ErrorState message={`Error: ${String(error)}`} />;

  const filteredLimits = limits?.filter((lim: RiskLimitResponse) => {
    if (lim.scope_type === 'GLOBAL') return true;
    if (lim.scope_type === 'PORTFOLIO') {
      return lim.scope_value === String(portfolioId);
    }
    return true;
  });

  return (
    <div>
      <PageHeader title="Risk Limits" description="Global and portfolio-specific risk constraints" />

      <ModelStatusBanner variant="info" status="Demonstration Policy" message="These seeded limits are for demonstration purposes only." />

      <DataPanel noPad>
        <TablePanel>
          <thead>
            <tr>
              <Th>Code</Th><Th>Name</Th><Th>Metric</Th><Th>Scope</Th>
              <Th right>Threshold</Th><Th>Direction</Th><Th>Status</Th><Th>Action</Th>
            </tr>
          </thead>
          <tbody>
            {filteredLimits?.map((lim: RiskLimitResponse) => (
              <tr key={lim.id} style={{ opacity: lim.is_active ? 1 : 0.45 }}>
                <Td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{lim.code}</Td>
                <Td>{lim.name}</Td>
                <Td>{lim.metric_type}</Td>
                <Td>{lim.scope_type} {lim.scope_value}</Td>
                <Td right mono>{lim.limit_threshold}</Td>
                <Td>{lim.direction}</Td>
                <Td><StatusBadge label={lim.is_active ? 'Active' : 'Inactive'} variant={lim.is_active ? 'ok' : 'muted'} /></Td>
                <Td>
                  {lim.is_active && (
                    <Btn variant="danger" size="sm" onClick={() => deactivateMutation.mutate(lim.id)} disabled={deactivateMutation.isPending}>
                      Deactivate
                    </Btn>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </TablePanel>
      </DataPanel>
    </div>
  );
};
