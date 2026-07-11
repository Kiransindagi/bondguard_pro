import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLatestAnalytics, getAnalyticsHistory, triggerAnalyticsRun } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, EmptyState, TablePanel, Th, Td, Btn, StatusBadge, KVRow } from '../components/ui';

const inputStyle: React.CSSProperties = {
  padding: '7px 12px', borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
  border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '11px',
};

const fmtCcy = (v: any) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const AnalyticsRuns = () => {
  const queryClient = useQueryClient();
  const { selectedPortfolioId: portfolioId } = usePortfolio();
  const [valuationDate, setValuationDate] = useState<string>(new Date().toISOString().split('T')[0]);

  const { data: latest, isLoading: isLatestLoading, isError: isLatestError, refetch: refetchLatest } = useQuery({ queryKey: ['latestAnalytics', portfolioId], queryFn: () => getLatestAnalytics(portfolioId!), enabled: !!portfolioId });
  const { data: history, isLoading: isHistoryLoading, refetch: refetchHistory } = useQuery({ queryKey: ['analyticsHistory', portfolioId], queryFn: () => getAnalyticsHistory(portfolioId!), enabled: !!portfolioId });

  const mutation = useMutation({
    mutationFn: (dateVal: string) => triggerAnalyticsRun(portfolioId!, dateVal),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['latestAnalytics', portfolioId] }); queryClient.invalidateQueries({ queryKey: ['analyticsHistory', portfolioId] }); },
  });

  if (!portfolioId) return <><PageHeader title="Analytics Runs" description="Batch valuation pipeline and quantitative risk runs" /><EmptyState message="No portfolio selected." /></>;

  return (
    <div>
      <PageHeader
        title="Analytics Runs"
        description="Batch valuation pipeline and quantitative risk runs"
        action={
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input type="date" value={valuationDate} onChange={e => setValuationDate(e.target.value)} style={inputStyle} />
            <Btn variant="primary" size="sm" onClick={() => mutation.mutate(valuationDate)} disabled={mutation.isPending}>
              {mutation.isPending ? 'Calculating...' : 'Run Valuation Batch'}
            </Btn>
            <Btn variant="ghost" size="sm" onClick={() => { refetchLatest(); refetchHistory(); }}>Refresh</Btn>
          </div>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', marginBottom: '24px' }}>
        {/* Latest Summary */}
        <div>
          <SectionHeader title="Latest Valuation Summary" />
          {isLatestLoading ? <LoadingState /> : isLatestError || !latest?.snapshot ? (
            <DataPanel><EmptyState message="No batch evaluations run yet." /></DataPanel>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <MetricCard label="Valuation Status" value={latest.run.status}
                  accent={latest.run.status === 'SUCCESS'} warning={latest.run.status === 'PARTIAL_SUCCESS'} danger={latest.run.status === 'FAILED'} />
                <MetricCard label="Model Status" value={latest.snapshot.market_risk_model_status.replace('_', ' ')}
                  accent={latest.snapshot.market_risk_model_status === 'FULL_FACTOR_MODEL'} warning={latest.snapshot.market_risk_model_status === 'RATE_ONLY_MODEL'} />
                <MetricCard label="Data Quality" value={latest.run.data_quality_status}
                  accent={latest.run.data_quality_status === 'PASS'} warning={latest.run.data_quality_status === 'WARNING'} danger={latest.run.data_quality_status === 'FAILED'} />
              </div>

              <DataPanel title="Metrics Snapshot" noPad>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', padding: '16px 20px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <KVRow label="Market Value" value={fmtCcy(latest.snapshot.total_market_value)} />
                    <KVRow label="Unrealized P&L" value={<span style={{ color: Number(latest.snapshot.total_unrealized_pnl) >= 0 ? 'var(--text-positive)' : 'var(--text-critical)' }}>{fmtCcy(latest.snapshot.total_unrealized_pnl)}</span>} />
                    <KVRow label="Portfolio YTM" value={`${(latest.snapshot.weighted_ytm * 100).toFixed(2)}%`} />
                    <KVRow label="Modified Duration" value={`${latest.snapshot.weighted_modified_duration.toFixed(2)} yrs`} />
                    <KVRow label="Total DV01" value={`$${Number(latest.snapshot.total_dv01).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <KVRow label="Historical VaR (95%)" value={latest.snapshot.historical_var_95_1d ? `$${Number(latest.snapshot.historical_var_95_1d).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'} />
                    <KVRow label="Expected Shortfall" value={latest.snapshot.expected_shortfall_95_1d ? `$${Number(latest.snapshot.expected_shortfall_95_1d).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'} />
                    <KVRow label="Liquidity Score" value={latest.snapshot.weighted_liquidity_score ? `${latest.snapshot.weighted_liquidity_score.toFixed(2)} / 100` : 'N/A'} />
                    <KVRow label="Liquidation Cost" value={latest.snapshot.liquidation_cost ? `$${Number(latest.snapshot.liquidation_cost).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'} />
                    <KVRow label="Limit Breach Status" value={<span style={{ fontWeight: 600, color: latest.snapshot.overall_limit_status === 'PASS' ? 'var(--text-positive)' : 'var(--text-critical)' }}>{latest.snapshot.overall_limit_status} ({latest.snapshot.open_breach_count})</span>} />
                  </div>
                </div>
              </DataPanel>
            </div>
          )}
        </div>

        {/* Valuation Context Panel */}
        <div>
          <SectionHeader title="Valuation Context" />
          {latest?.run ? (
            <DataPanel>
              <KVRow label="As of Date" value={latest.run.valuation_date} />
              <KVRow label="Calculated At" value={new Date(latest.run.started_at).toLocaleString()} />
              <KVRow label="Market Data Date" value={latest.run.metadata_json?.market_data_as_of || 'N/A'} />

              <div style={{ marginTop: '16px' }}>
                <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Model Governance</span>
                {!latest.run.metadata_json?.degraded_models?.length ? (
                  <span style={{ fontSize: '11px', color: 'var(--text-positive)' }}>✓ All models aligned</span>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {latest.run.metadata_json.degraded_models.map((m: string) => <span key={m} style={{ fontSize: '11px', color: 'var(--text-warning)' }}>⚠️ {m} degraded</span>)}
                  </div>
                )}
              </div>
              
              {latest.run.error_summary && (
                <div style={{ marginTop: '16px', padding: '10px', backgroundColor: 'var(--bg-inset)', borderLeft: '3px solid var(--text-critical)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-critical)', marginBottom: '4px' }}>Batch Warnings</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{latest.run.error_summary}</div>
                </div>
              )}
            </DataPanel>
          ) : <DataPanel><EmptyState message="No context available" /></DataPanel>}
        </div>
      </div>

      {/* History */}
      <SectionHeader title="Runs History" />
      <DataPanel noPad>
        {isHistoryLoading ? <LoadingState /> : !history || history.length === 0 ? <EmptyState message="No batch evaluations recorded." /> : (
          <TablePanel>
            <thead><tr><Th>Run ID</Th><Th>Valuation Date</Th><Th>Status</Th><Th>Model Status</Th><Th>Quality Status</Th><Th>Run Time</Th><Th>Diagnostic Summary</Th></tr></thead>
            <tbody>
              {history.map((run: any) => (
                <tr key={run.id}>
                  <Td style={{ fontWeight: 600 }}>#{run.id}</Td>
                  <Td>{run.valuation_date}</Td>
                  <Td><StatusBadge label={run.status} variant={run.status === 'SUCCESS' ? 'ok' : run.status === 'PARTIAL_SUCCESS' ? 'warning' : 'danger'} /></Td>
                  <Td><StatusBadge label={run.model_status || 'N/A'} variant={run.model_status === 'RATE_ONLY_MODEL' ? 'warning' : 'info'} /></Td>
                  <Td><StatusBadge label={run.data_quality_status || 'N/A'} variant={run.data_quality_status === 'PASS' ? 'ok' : run.data_quality_status === 'WARNING' ? 'warning' : 'danger'} /></Td>
                  <Td style={{ fontSize: '11px' }}>{new Date(run.started_at).toLocaleString()}</Td>
                  <Td style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{run.error_summary || 'OK'}</Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        )}
      </DataPanel>
    </div>
  );
};
export default AnalyticsRuns;
