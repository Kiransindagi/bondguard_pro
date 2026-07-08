
import { useQuery } from '@tanstack/react-query';
import { getPortfolioRiskReport, fetchPortfolioPositionsRisk, getFactorCorrelation } from '../api/client';

export const RiskIntelligence = () => {
  const portfolioId = 1;

  const { data: report, isLoading: isReportLoading } = useQuery({
    queryKey: ['riskReport', portfolioId],
    queryFn: () => getPortfolioRiskReport(portfolioId)
  });
  
  const { data: positionRisk, isLoading: isPosLoading } = useQuery({
    queryKey: ['portfolioPositionsRisk', portfolioId],
    queryFn: () => fetchPortfolioPositionsRisk(portfolioId)
  });

  const { data: correlationData, isLoading: isCorrLoading } = useQuery({
    queryKey: ['factorCorrelation', 'production_factors'],
    queryFn: () => getFactorCorrelation('production_factors')
  });

  if (isReportLoading || isPosLoading || isCorrLoading) return <div style={{ color: '#94a3b8' }}>Analyzing Risk Intelligence...</div>;
  if (!report) return <div style={{ color: '#ef4444' }}>Risk report unavailable. Please evaluate risk control first.</div>;

  // Analysis Logic
  let highestDv01Position = null;
  let highestDurationPosition = null;
  if (positionRisk && positionRisk.length > 0) {
    highestDv01Position = [...positionRisk].sort((a, b) => b.dv01 - a.dv01)[0];
    highestDurationPosition = [...positionRisk].sort((a, b) => b.modified_duration - a.modified_duration)[0];
  }

  const worstStress = report.stress_risk?.worst_scenario_name;
  const isMarketModelDegraded = report.model_governance?.degraded_models?.includes('MARKET_RISK_RATE_ONLY');
  const largestConcentration = report.concentration?.largest_issuer;
  
  const hasBreaches = report.active_breaches && report.active_breaches.length > 0;

  // Correlation Matrix Parsing
  let matrixFactors: string[] = [];
  let matrixData: any[] = [];
  if (correlationData && correlationData.data) {
    matrixFactors = Object.keys(correlationData.data[0]).filter(k => k !== 'factor');
    matrixData = correlationData.data;
  }

  const getHeatmapColor = (value: number) => {
    if (value > 0) {
      return `rgba(34, 197, 94, ${value})`;
    } else {
      return `rgba(239, 68, 68, ${Math.abs(value)})`;
    }
  };
  
  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e2e8f0' }}>Risk Intelligence</h1>
      <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>Deterministic insights compiled from analytical outputs.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Model Warnings */}
        {isMarketModelDegraded && (
          <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #eab308' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#eab308' }}>Degraded Model: RATE_ONLY_MODEL</h3>
            <p style={{ margin: 0, color: '#e2e8f0' }}>Credit spread risk is currently excluded because the aligned spread history is insufficient for full factor evaluation.</p>
          </div>
        )}

        {/* Breaches */}
        {hasBreaches && (
          <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#ef4444' }}>Active Limit Breaches</h3>
            <p style={{ margin: 0, color: '#e2e8f0' }}>There are {report.active_breaches.length} unacknowledged limit breaches requiring immediate attention.</p>
          </div>
        )}

        {/* Major Drivers */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Largest Risk Contributors</h3>
          {highestDv01Position ? (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ color: '#e2e8f0' }}><strong>Highest DV01:</strong> {highestDv01Position.bond_id}</div>
              <div style={{ color: '#64748b' }}>${highestDv01Position.dv01?.toFixed(2) ?? 'N/A'} per bp</div>
            </div>
          ) : null}
          {highestDurationPosition ? (
            <div>
              <div style={{ color: '#e2e8f0' }}><strong>Highest Duration:</strong> {highestDurationPosition.bond_id}</div>
              <div style={{ color: '#64748b' }}>{highestDurationPosition.modified_duration?.toFixed(2) ?? 'N/A'} yrs</div>
            </div>
          ) : null}
        </div>

        {/* Scenarios & Liquidity */}
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#94a3b8' }}>Vulnerabilities</h3>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ color: '#e2e8f0' }}><strong>Worst Stress Scenario:</strong></div>
            <div style={{ color: worstStress ? '#ef4444' : '#64748b' }}>{worstStress || 'None identified'}</div>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ color: '#e2e8f0' }}><strong>Largest Concentration:</strong></div>
            <div style={{ color: '#38bdf8' }}>{largestConcentration ? largestConcentration : 'None'}</div>
          </div>
          <div>
            <div style={{ color: '#e2e8f0' }}><strong>Liquidity Constraint:</strong></div>
            <div style={{ color: '#64748b' }}>Max days to liquidate: {report.liquidity_risk?.max_days_to_liquidate ? report.liquidity_risk.max_days_to_liquidate.toFixed(1) : 'N/A'} days</div>
          </div>
        </div>

      </div>

      <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0' }}>Production Risk Factor Correlation</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Linear correlation between production factors (Rates and Spreads). Excludes ETF market context.</p>
        
        {matrixFactors.length > 0 ? (
          <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '0.875rem', minWidth: '600px' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.5rem', color: '#64748b' }}></th>
                  {matrixFactors.map(f => <th key={f} style={{ padding: '0.5rem', color: '#64748b', fontWeight: 'normal', textAlign: 'center' }}>{f.replace('RATE_','').replace('SPREAD_','')}</th>)}
                </tr>
              </thead>
              <tbody>
                {matrixData.map((row: any) => (
                  <tr key={row.factor}>
                    <td style={{ padding: '0.5rem', color: '#e2e8f0', textAlign: 'right', whiteSpace: 'nowrap' }}>{row.factor.replace('RATE_','').replace('SPREAD_','')}</td>
                    {matrixFactors.map(f => {
                      const val = row[f];
                      return (
                        <td key={f} style={{ 
                          padding: '0.5rem', 
                          textAlign: 'center', 
                          backgroundColor: val !== null ? getHeatmapColor(val) : 'transparent',
                          color: val !== null && Math.abs(val) > 0.5 ? '#fff' : '#cbd5e1'
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
        ) : (
          <div style={{ color: '#94a3b8' }}>Correlation data unavailable.</div>
        )}
      </div>

    </div>
  );
};
