import { useQuery } from '@tanstack/react-query';
import { getPortfolioRiskReport, fetchPortfolioPositionsRisk, getFactorCorrelation } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, DataPanel, SectionHeader, ModelStatusBanner, LoadingState, ErrorState, KVRow, EmptyState } from '../components/ui';

export const RiskIntelligence = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();
  const { data: report, isLoading: isReportLoading } = useQuery({ queryKey: ['riskReport', portfolioId], queryFn: () => getPortfolioRiskReport(portfolioId!), enabled: !!portfolioId });
  const { data: positionRisk, isLoading: isPosLoading } = useQuery({ queryKey: ['portfolioPositionsRisk', portfolioId], queryFn: () => fetchPortfolioPositionsRisk(portfolioId!), enabled: !!portfolioId });
  const { data: correlationData, isLoading: isCorrLoading } = useQuery({ queryKey: ['factorCorrelation', 'production_factors'], queryFn: () => getFactorCorrelation('production_factors'), enabled: !!portfolioId });

  if (!portfolioId) return <><PageHeader title="Risk Intelligence" description="Deterministic insights compiled from analytical outputs" /><EmptyState message="No portfolio selected." /></>;
  if (isReportLoading || isPosLoading || isCorrLoading) return <LoadingState message="Analyzing Risk Intelligence..." />;
  if (!report) return <ErrorState message="Risk report unavailable. Please evaluate risk control first." />;

  let highestDv01Position: any = null, highestDurationPosition: any = null;
  if (positionRisk && positionRisk.length > 0) {
    highestDv01Position = [...positionRisk].sort((a: any, b: any) => b.dv01 - a.dv01)[0];
    highestDurationPosition = [...positionRisk].sort((a: any, b: any) => b.modified_duration - a.modified_duration)[0];
  }

  const isMarketModelDegraded = report.model_governance?.degraded_models?.includes('MARKET_RISK_RATE_ONLY');
  const hasBreaches = report.active_breaches && report.active_breaches.length > 0;

  let matrixFactors: string[] = [];
  let matrixData: any[] = [];
  if (correlationData?.data) {
    matrixFactors = Object.keys(correlationData.data[0]).filter((k: string) => k !== 'factor');
    matrixData = correlationData.data;
  }

  const getHeatmapColor = (v: number) => v > 0 ? `rgba(52,211,153,${v})` : `rgba(248,113,113,${Math.abs(v)})`;

  return (
    <div>
      <PageHeader title="Risk Intelligence" description="Deterministic insights compiled from analytical outputs" />

      {isMarketModelDegraded && (
        <ModelStatusBanner status="Degraded Model: RATE_ONLY_MODEL" message="Credit spread risk is currently excluded due to insufficient aligned spread history." />
      )}

      {hasBreaches && (
        <ModelStatusBanner variant="danger" status="Active Limit Breaches" message={`${report.active_breaches.length} unacknowledged limit breaches require attention.`} />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
        <DataPanel title="Key Risk Drivers">
          {highestDv01Position ? (
            <KVRow label="Highest DV01" value={<><span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Bond {highestDv01Position.bond_id}</span> <span style={{ color: 'var(--text-muted)' }}>${highestDv01Position.dv01?.toFixed(2) ?? 'N/A'} per bp</span></>} />
          ) : null}
          {highestDurationPosition ? (
            <KVRow label="Highest Duration" value={<><span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Bond {highestDurationPosition.bond_id}</span> <span style={{ color: 'var(--text-muted)' }}>{highestDurationPosition.modified_duration?.toFixed(2) ?? 'N/A'} yrs</span></>} />
          ) : null}
        </DataPanel>

        <DataPanel title="Vulnerabilities">
          <KVRow label="Worst Stress Scenario" value={
            <span style={{ color: report.stress_risk?.worst_scenario_name ? 'var(--text-critical)' : 'var(--text-muted)' }}>
              {report.stress_risk?.worst_scenario_name || 'None identified'}
            </span>
          } />
          <KVRow label="Largest Concentration" value={report.concentration?.largest_issuer || 'None'} />
          <KVRow label="Max Days to Liquidate" value={
            report.liquidity_risk?.max_days_to_liquidate ? `${report.liquidity_risk.max_days_to_liquidate.toFixed(1)} days` : 'N/A'
          } />
        </DataPanel>
      </div>

      {/* Correlation Matrix */}
      <SectionHeader title="Production Risk Factor Correlation" />
      <DataPanel>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px' }}>
          Linear correlation between production factors (Rates and Spreads). Excludes ETF market context.
        </p>
        {matrixFactors.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '11px', minWidth: '500px' }}>
              <thead>
                <tr>
                  <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontWeight: 500 }}></th>
                  {matrixFactors.map(f => <th key={f} style={{ padding: '6px 10px', color: 'var(--text-muted)', fontWeight: 500, textAlign: 'center' }}>{f.replace('RATE_','').replace('SPREAD_','')}</th>)}
                </tr>
              </thead>
              <tbody>
                {matrixData.map((row: any) => (
                  <tr key={row.factor}>
                    <td style={{ padding: '6px 10px', color: 'var(--text-primary)', textAlign: 'right', whiteSpace: 'nowrap', fontWeight: 500 }}>{row.factor.replace('RATE_','').replace('SPREAD_','')}</td>
                    {matrixFactors.map(f => {
                      const val = row[f];
                      return (
                        <td key={f} style={{
                          padding: '6px 10px', textAlign: 'center',
                          backgroundColor: val !== null ? getHeatmapColor(val) : 'transparent',
                          color: val !== null && Math.abs(val) > 0.5 ? '#fff' : 'var(--text-secondary)',
                          fontVariantNumeric: 'tabular-nums',
                        }}>
                          {val !== null ? val.toFixed(2) : '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState message="Correlation data unavailable." />}
      </DataPanel>
    </div>
  );
};
