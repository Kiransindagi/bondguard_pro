import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSnapshots, getExecutiveReport, generateSnapshot } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, ModelStatusBanner, LoadingState, EmptyState, TablePanel, Th, Td, Btn } from '../components/ui';

export const Reporting = () => {
  const queryClient = useQueryClient();
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: snapshots, isLoading: snapsLoading } = useQuery({ queryKey: ['snapshots', portfolioId], queryFn: () => getSnapshots(portfolioId!), enabled: !!portfolioId });
  const { data: latestReport, isLoading: reportLoading } = useQuery({ queryKey: ['executiveReport', portfolioId], queryFn: () => getExecutiveReport(portfolioId!), enabled: !!portfolioId });
  const generateMutation = useMutation({
    mutationFn: () => generateSnapshot(portfolioId!),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['snapshots', portfolioId] }); queryClient.invalidateQueries({ queryKey: ['executiveReport', portfolioId] }); },
  });

  if (!portfolioId) return <><PageHeader title="Executive Reporting" description="Historical risk snapshots and institutional report generation" /><EmptyState message="No portfolio selected." /></>;
  if (snapsLoading || reportLoading) return <LoadingState message="Loading Reporting..." />;

  const fmtCcy = (v: any) => `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div>
      <PageHeader
        title="Executive Reporting"
        description="Historical risk snapshots and institutional report generation"
        action={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn variant="primary" size="sm" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
              {generateMutation.isPending ? 'Generating...' : 'Generate Snapshot'}
            </Btn>
            <Btn variant="secondary" size="sm" onClick={() => window.open(`http://localhost:8000/api/v1/reporting/portfolios/${portfolioId}/executive-report.csv`, '_blank')}>CSV</Btn>
            <Btn variant="secondary" size="sm" onClick={() => window.open(`http://localhost:8000/api/v1/reporting/portfolios/${portfolioId}/executive-report.pdf`, '_blank')}>PDF</Btn>
          </div>
        }
      />

      {latestReport?.executive_summary && (
        <>
          <SectionHeader title="Latest Executive Summary" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
            <MetricCard label="Overall Status" value={latestReport.executive_summary.overall_risk_status}
              accent={latestReport.executive_summary.overall_risk_status === 'PASS'}
              danger={latestReport.executive_summary.overall_risk_status !== 'PASS'} />
            <MetricCard label="Open Breaches" value={String(latestReport.executive_summary.number_of_open_breaches)}
              danger={latestReport.executive_summary.number_of_open_breaches > 0} />
            <MetricCard label="Model Status" value={latestReport.executive_summary.market_risk_model_status}
              warning={latestReport.executive_summary.market_risk_model_status === 'RATE_ONLY_MODEL'} />
            <MetricCard label="Largest Contributor" value={latestReport.executive_summary.largest_risk_contributor || 'N/A'} />
          </div>

          {latestReport.model_governance?.limitations?.length > 0 && (
            <ModelStatusBanner variant="warning" status="Model Governance" message={latestReport.model_governance.limitations.join(' | ')} />
          )}
        </>
      )}

      {/* Historical snapshots */}
      <SectionHeader title="Historical Snapshots" />
      {snapshots && snapshots.length > 0 ? (
        <DataPanel noPad>
          <TablePanel>
            <thead>
              <tr><Th>Date</Th><Th right>Market Value</Th><Th right>Mod Dur</Th><Th right>DV01</Th><Th right>Hist VaR (95%)</Th><Th right>Open Breaches</Th></tr>
            </thead>
            <tbody>
              {snapshots.map((s: any) => (
                <tr key={s.id}>
                  <Td>{s.snapshot_date}</Td>
                  <Td right mono>{fmtCcy(s.total_market_value)}</Td>
                  <Td right mono>{Number(s.weighted_modified_duration).toFixed(2)}</Td>
                  <Td right mono>{fmtCcy(s.total_dv01)}</Td>
                  <Td right mono>{s.historical_var_95_1d !== null ? fmtCcy(s.historical_var_95_1d) : 'N/A'}</Td>
                  <Td right mono>{s.open_breach_count}</Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        </DataPanel>
      ) : <EmptyState message="No historical snapshots available." />}
    </div>
  );
};
