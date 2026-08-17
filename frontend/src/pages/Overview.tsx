import { useQuery } from '@tanstack/react-query';
import { fetchPortfolioSummary, fetchPortfolioRiskSummary, getPortfolioRiskReport, getSnapshots } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { PageHeader, MetricCard, DataPanel, SectionHeader, StatusBadge, ModelStatusBanner, LoadingState, EmptyState, KVRow } from '../components/ui';
import { RC_GRID_PROPS, RC_AXIS_STYLE, RC_TOOLTIP_STYLE, RC_LEGEND_STYLE, CHART_COLORS } from '../lib/plotlyTheme';

export const Overview = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: summary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['portfolioSummary', portfolioId],
    queryFn: () => fetchPortfolioSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: riskSummary, isLoading: isRiskLoading } = useQuery({
    queryKey: ['portfolioRiskSummary', portfolioId],
    queryFn: () => fetchPortfolioRiskSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: report, isLoading: isReportLoading } = useQuery({
    queryKey: ['riskReport', portfolioId],
    queryFn: () => getPortfolioRiskReport(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: snapshots, isLoading: isSnapshotsLoading } = useQuery({
    queryKey: ['snapshots', portfolioId],
    queryFn: () => getSnapshots(portfolioId!),
    enabled: !!portfolioId,
  });

  const fmtCurrency = (v: any) => '$' + Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmtNum = (v: any, d = 2) => Number(v || 0).toFixed(d);
  const limitTone = (status: string) => status === 'BREACH' ? 'var(--text-critical)' : status === 'WARNING' ? 'var(--text-warning)' : 'var(--text-positive)';

  if (!portfolioId) {
    return (
      <div>
        <PageHeader title="Executive Overview" description="Real-time portfolio risk and performance summary" />
        <EmptyState message="No portfolio selected. Please select a portfolio to view overview." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Executive Overview"
        description="Real-time portfolio risk and performance summary"
        context={`${summary ? summary.name : 'No Portfolio'}  |  ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}`}
      />

      {/* ── Core metrics strip ──────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        <MetricCard
          label="Total Market Value"
          value={isSummaryLoading ? '...' : summary ? fmtCurrency(summary.total_market_value) : 'N/A'}
          accent
        />
        <MetricCard
          label="Unrealized P&L"
          value={isSummaryLoading ? '...' : summary ? fmtCurrency(summary.total_pnl) : 'N/A'}
          sub={summary && Number(summary.total_pnl) >= 0 ? 'Gain' : 'Loss'}
          accent={summary && Number(summary.total_pnl) >= 0}
          danger={summary && Number(summary.total_pnl) < 0}
        />
        <MetricCard
          label="Modified Duration"
          value={isRiskLoading ? '...' : riskSummary ? fmtNum(riskSummary.weighted_modified_duration) : 'N/A'}
          unit="yrs"
        />
        <MetricCard
          label="Total DV01"
          value={isRiskLoading ? '...' : riskSummary ? fmtCurrency(riskSummary.total_dv01) : 'N/A'}
        />
        <MetricCard
          label="VaR (95% 1d)"
          value={isReportLoading ? '...' : report?.market_risk?.historical_var !== null && report?.market_risk?.historical_var !== undefined
            ? fmtCurrency(report.market_risk.historical_var) : 'N/A'}
          warning={report?.market_risk?.model_status === 'RATE_ONLY_MODEL'}
        />
        <MetricCard
          label="Active Breaches"
          value={isReportLoading ? '...' : report?.breach_summary ? String(report.breach_summary.open_count) : '0'}
          danger={report?.breach_summary && report.breach_summary.open_count > 0}
        />
      </div>

      {/* ── Model health strip ──────────────────────────────────── */}
      {report?.model_governance && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
          <StatusBadge label={`Risk Control: ${report.report_metadata?.overall_status || 'N/A'}`}
            variant={report.report_metadata?.overall_status === 'BREACH' ? 'danger' : report.report_metadata?.overall_status === 'WARNING' ? 'warning' : 'ok'} />
          <StatusBadge label={`Market Risk: ${report.market_risk?.model_status || 'N/A'}`}
            variant={report.market_risk?.model_status === 'RATE_ONLY_MODEL' ? 'warning' : report.market_risk?.model_status === 'AVAILABLE' ? 'ok' : 'muted'} />
          {report.model_governance.degraded_models?.map((m: string) => (
            <StatusBadge key={m} label={`${m}: Degraded`} variant="warning" />
          ))}
          {report.model_governance.proxy_models?.map((m: string) => (
            <StatusBadge key={m} label={`${m}: Proxy`} variant="info" />
          ))}
        </div>
      )}

      {report?.market_risk?.model_status === 'RATE_ONLY_MODEL' && (
        <ModelStatusBanner
          status="Rate-Only Model Active"
          message="Credit spread history insufficient. VaR calculation excludes credit spread risk factors."
        />
      )}

      {/* ── Mid-section: Stress + Liquidity + Governance ────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px', marginBottom: '28px' }}>
        {/* Stress Testing */}
        <DataPanel title="Stress Testing">
          {isReportLoading ? <LoadingState /> : !report?.stress_risk ? <EmptyState /> : (
            <div>
              <KVRow label="Worst Scenario" value={report.stress_risk.worst_scenario_name || 'N/A'} />
              <KVRow label="Worst Loss" value={
                report.stress_risk.pnl !== null
                  ? <span style={{ color: 'var(--text-critical)' }}>-{fmtCurrency(Math.abs(Number(report.stress_risk.pnl)))}</span>
                  : 'N/A'
              } />
            </div>
          )}
        </DataPanel>

        {/* Liquidity */}
        <DataPanel title="Liquidity Profile">
          {isReportLoading ? <LoadingState /> : !report?.liquidity_risk ? <EmptyState /> : (
            <div>
              <KVRow label="Liquidity Score" value={
                report.liquidity_risk.liquidity_score !== null
                  ? `${fmtNum(report.liquidity_risk.liquidity_score)} / 100` : 'N/A'
              } />
              <KVRow label="Largest Concentration" value={
                `${report.concentration?.largest_issuer || 'N/A'} (${fmtNum(Number(report.concentration?.largest_issuer_weight || 0) * 100, 1)}%)`
              } />
            </div>
          )}
        </DataPanel>

        {/* Governance */}
        <DataPanel title="Model Governance">
          {isReportLoading ? <LoadingState /> : !report?.model_governance ? <EmptyState /> : (
            <div>
              <KVRow label="Market Risk Model" value={
                <StatusBadge
                  label={report.market_risk?.model_status || 'N/A'}
                  variant={report.market_risk?.model_status === 'RATE_ONLY_MODEL' ? 'warning' : 'ok'}
                />
              } />
              {report.model_governance.degraded_models?.map((m: string) => (
                <KVRow key={m} label={m} value={<StatusBadge label="Degraded" variant="warning" />} />
              ))}
              {report.model_governance.proxy_models?.map((m: string) => (
                <KVRow key={m} label={m} value={<StatusBadge label="Proxy" variant="info" />} />
              ))}
            </div>
          )}
        </DataPanel>
      </div>

      <DataPanel title="Risk Limit Utilization" style={{ marginBottom: '28px' }} headerAction={<span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Latest evaluated limits</span>}>
        {isReportLoading ? <LoadingState /> : !report?.limit_results?.length ? <EmptyState message="No risk-limit evaluation is available." /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px, 1fr))', gap: '12px' }}>
            {report.limit_results.slice(0, 6).map((limit: any) => {
              const utilization = Math.max(0, Number(limit.utilization_percent || 0) * 100);
              const tone = limitTone(limit.status);
              return (
                <div key={`${limit.metric_type}-${limit.threshold_value}`} style={{ backgroundColor: 'var(--bg-inset)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(limit.metric_type).replaceAll('_', ' ')}</span>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: tone }}>{limit.status}</span>
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{utilization.toFixed(0)}%</div>
                  <div style={{ height: '5px', backgroundColor: 'rgba(148,163,184,0.16)', borderRadius: '999px', marginTop: '10px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(utilization, 100)}%`, height: '100%', backgroundColor: tone, borderRadius: 'inherit' }} />
                  </div>
                  <div style={{ marginTop: '7px', fontSize: '10px', color: 'var(--text-muted)' }}>Limit: {Number(limit.threshold_value).toLocaleString('en-US')}</div>
                </div>
              );
            })}
          </div>
        )}
      </DataPanel>

      {/* ── Historical Trend Charts ─────────────────────────────── */}
      <SectionHeader title="Historical Risk Trends" />

      {isSnapshotsLoading ? <LoadingState message="Loading historical data..." /> : (!snapshots || snapshots.length <= 1) ? (
        <DataPanel><EmptyState message="Historical trend data requires additional snapshots." /></DataPanel>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          {[
            { key: 'total_market_value', title: 'Portfolio Market Value', color: CHART_COLORS.accent, fmt: (v: any) => `$${(v/1000000).toFixed(1)}M` },
            { key: 'weighted_modified_duration', title: 'Modified Duration', color: CHART_COLORS.primary, fmt: undefined },
            { key: 'total_dv01', title: 'Total DV01', color: CHART_COLORS.amber, fmt: undefined },
          ].map(chart => (
            <DataPanel key={chart.key} title={chart.title}>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={snapshots}>
                  <CartesianGrid {...RC_GRID_PROPS} />
                  <XAxis dataKey="snapshot_date" {...RC_AXIS_STYLE} />
                  <YAxis {...RC_AXIS_STYLE} tickFormatter={chart.fmt} />
                  <RechartsTooltip {...RC_TOOLTIP_STYLE} />
                  <Line type="monotone" dataKey={chart.key} stroke={chart.color} strokeWidth={2} dot={{ r: 2, fill: chart.color }} />
                </LineChart>
              </ResponsiveContainer>
            </DataPanel>
          ))}

          <DataPanel title="VaR (95%) & Breach Count">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={snapshots}>
                <CartesianGrid {...RC_GRID_PROPS} />
                <XAxis dataKey="snapshot_date" {...RC_AXIS_STYLE} />
                <YAxis yAxisId="left" {...RC_AXIS_STYLE} />
                <YAxis yAxisId="right" orientation="right" {...RC_AXIS_STYLE} />
                <RechartsTooltip {...RC_TOOLTIP_STYLE} />
                <Legend {...RC_LEGEND_STYLE} />
                <Line yAxisId="left" type="monotone" dataKey="historical_var_95_1d" name="VaR 95%" stroke={CHART_COLORS.purple} strokeWidth={2} dot={{ r: 2 }} connectNulls />
                <Line yAxisId="right" type="monotone" dataKey="open_breach_count" name="Open Breaches" stroke={CHART_COLORS.red} strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </DataPanel>
        </div>
      )}
    </div>
  );
};
