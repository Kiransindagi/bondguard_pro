import { useQuery } from '@tanstack/react-query';
import { fetchPortfolioSummary, fetchPortfolioPositions } from '../api/client';
import { usePortfolio } from '../auth/PortfolioContext';
import { PageHeader, MetricCard, SectionHeader, DataPanel, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td } from '../components/ui';

export const Portfolio = () => {
  const { selectedPortfolioId: portfolioId } = usePortfolio();

  const { data: summary, isLoading: loadingSummary, isError: errorSummary } = useQuery({
    queryKey: ['portfolioSummary', portfolioId],
    queryFn: () => fetchPortfolioSummary(portfolioId!),
    enabled: !!portfolioId,
  });

  const { data: positions, isLoading: loadingPos, isError: errorPos } = useQuery({
    queryKey: ['portfolioPositions', portfolioId],
    queryFn: () => fetchPortfolioPositions(portfolioId!),
    enabled: !!portfolioId,
  });

  if (!portfolioId) return <EmptyState message="No portfolio selected." />;

  const fmtCcy = (v: any) => '$' + Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

  return (
    <div>
      <PageHeader title="Portfolio Overview" description="Holdings, valuation, and position detail" />

      {loadingSummary ? <LoadingState message="Loading portfolio summary..." /> : errorSummary ? <ErrorState message="Error loading portfolio summary." /> : summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '28px' }}>
          <MetricCard label="Portfolio" value={summary.name} />
          <MetricCard label="Total Market Value" value={fmtCcy(summary.total_market_value)} accent />
          <MetricCard
            label="Unrealized P&L"
            value={fmtCcy(summary.total_unrealized_pnl)}
            accent={summary.total_unrealized_pnl >= 0}
            danger={summary.total_unrealized_pnl < 0}
          />
          <MetricCard label="Positions" value={String(summary.position_count)} />
        </div>
      )}

      <SectionHeader title="Positions" />

      {loadingPos ? <LoadingState message="Loading positions..." /> : errorPos ? <ErrorState message="Error loading positions." /> : positions && positions.length > 0 ? (
        <DataPanel noPad>
          <TablePanel>
            <thead>
              <tr>
                <Th>Bond</Th><Th>Issuer</Th><Th>Rating</Th><Th>Maturity</Th>
                <Th right>Coupon</Th><Th right>Qty</Th><Th right>Avg Cost</Th>
                <Th right>Price</Th><Th right>Market Value</Th><Th right>P&L</Th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos: any) => (
                <tr key={pos.id}>
                  <Td>{pos.bond.ticker || pos.bond.isin}</Td>
                  <Td>{pos.bond.issuer_name}</Td>
                  <Td>{pos.bond.credit_rating || 'NR'}</Td>
                  <Td>{pos.bond.maturity_date}</Td>
                  <Td right mono>{(pos.bond.coupon_rate * 100).toFixed(2)}%</Td>
                  <Td right mono>{pos.quantity}</Td>
                  <Td right mono>${Number(pos.average_cost).toFixed(2)}</Td>
                  <Td right mono>${Number(pos.current_clean_price).toFixed(2)}</Td>
                  <Td right mono>{fmtCcy(pos.market_value)}</Td>
                  <Td right mono style={{ color: pos.unrealized_pnl >= 0 ? 'var(--text-positive)' : 'var(--text-critical)' }}>
                    {fmtCcy(pos.unrealized_pnl)}
                  </Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        </DataPanel>
      ) : <EmptyState message="No positions held." />}
    </div>
  );
};
