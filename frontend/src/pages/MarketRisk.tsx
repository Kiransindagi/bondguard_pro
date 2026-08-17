import { useQuery } from '@tanstack/react-query';
import { fetchPortfolioRiskSummary, fetchPortfolioPositionsRisk } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, DataPanel, SectionHeader, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td } from '../components/ui';

export const MarketRisk = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: summary, isLoading: loadingSummary, isError: errorSummary } = useQuery({
    queryKey: ['portfolioRiskSummary', portfolioId],
    queryFn: () => fetchPortfolioRiskSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: positions, isLoading: loadingPos, isError: errorPos } = useQuery({
    queryKey: ['portfolioPositionsRisk', portfolioId],
    queryFn: () => fetchPortfolioPositionsRisk(portfolioId!),
    enabled: !!portfolioId,
  });

  if (!portfolioId) return <EmptyState message="No portfolio selected." />;

  const fmtCcy = (v: any) => '$' + Number(v || 0).toLocaleString('en-US', { maximumFractionDigits: 2 });

  return (
    <div>
      <PageHeader
        title="Market Risk"
        description="Duration, convexity, and portfolio-level risk analytics"
        context={summary ? `Valuation: ${summary.valuation_date}${summary.curve_date ? ` | Curve: ${summary.curve_date}` : ''}` : undefined}
      />

      {loadingSummary ? <LoadingState message="Loading risk summary..." /> : errorSummary ? <ErrorState message="Error loading risk summary." /> : summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '28px' }}>
          <MetricCard label="Total Market Value" value={fmtCcy(summary.total_market_value)} accent />
          <MetricCard label="Weighted YTM" value={`${(Number(summary.weighted_average_ytm || 0) * 100).toFixed(2)}%`} />
          <MetricCard label="Modified Duration" value={Number(summary.weighted_modified_duration || 0).toFixed(2)} unit="yrs" />
          <MetricCard label="Convexity" value={Number(summary.weighted_convexity || 0).toFixed(2)} />
          <MetricCard label="Total DV01" value={fmtCcy(summary.total_dv01)} />
        </div>
      )}

      <SectionHeader title="Position Risk Table" />

      {loadingPos ? <LoadingState message="Loading position risks..." /> : errorPos ? <ErrorState message="Error loading position risks." /> : positions && positions.length > 0 ? (
        <DataPanel noPad>
          <TablePanel>
            <thead>
              <tr>
                <Th>Bond ID</Th>
                <Th right>Market Value</Th>
                <Th right>Price</Th>
                <Th right>YTM</Th>
                <Th right>Mod Dur</Th>
                <Th right>Convexity</Th>
                <Th right>DV01</Th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos: any) => (
                <tr key={pos.bond_id}>
                  <Td>{pos.bond_id}</Td>
                  <Td right mono>{fmtCcy(pos.market_value)}</Td>
                  <Td right mono>${Number(pos.clean_price).toFixed(2)}</Td>
                  <Td right mono>{(pos.ytm_decimal * 100).toFixed(2)}%</Td>
                  <Td right mono>{Number(pos.modified_duration_years).toFixed(2)}</Td>
                  <Td right mono>{Number(pos.convexity).toFixed(2)}</Td>
                  <Td right mono>{fmtCcy(pos.dv01_currency)}</Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        </DataPanel>
      ) : <EmptyState message="No active positions found." />}
    </div>
  );
};
