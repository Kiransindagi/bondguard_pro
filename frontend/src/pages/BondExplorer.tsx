import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBonds } from '../api/client';
import { PageHeader, DataPanel, LoadingState, ErrorState, EmptyState, TablePanel, Th, Td } from '../components/ui';

const inputStyle: React.CSSProperties = {
  padding: '8px 12px', borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border-muted)', backgroundColor: 'var(--bg-inset)',
  color: 'var(--text-primary)', fontSize: '12px', fontFamily: 'var(--font-sans)',
};

export const BondExplorer = () => {
  const [issuer, setIssuer] = useState('');
  const [rating, setRating] = useState('');
  const [sector, setSector] = useState('');

  const { data: bonds, isLoading, isError } = useQuery({
    queryKey: ['bonds', issuer, rating, sector],
    queryFn: () => {
      const filters: Record<string, string> = {};
      if (issuer) filters.issuer = issuer;
      if (rating) filters.rating = rating;
      if (sector) filters.sector = sector;
      return fetchBonds(filters);
    },
  });

  return (
    <div>
      <PageHeader title="Bond Explorer" description="Search and filter the bond universe" />

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input type="text" placeholder="Filter by Issuer..." value={issuer} onChange={e => setIssuer(e.target.value)} style={inputStyle} />
        <input type="text" placeholder="Filter by Rating..." value={rating} onChange={e => setRating(e.target.value)} style={inputStyle} />
        <input type="text" placeholder="Filter by Sector..." value={sector} onChange={e => setSector(e.target.value)} style={inputStyle} />
      </div>

      {isLoading ? <LoadingState message="Loading bonds..." /> : isError ? <ErrorState message="Error loading bonds." /> : bonds && bonds.length > 0 ? (
        <DataPanel noPad>
          <TablePanel>
            <thead>
              <tr>
                <Th>ISIN</Th><Th>Ticker</Th><Th>Issuer</Th><Th>Rating</Th>
                <Th>Maturity</Th><Th right>Coupon</Th><Th>Sector</Th>
              </tr>
            </thead>
            <tbody>
              {bonds.map((bond: any) => (
                <tr key={bond.id}>
                  <Td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{bond.isin}</Td>
                  <Td>{bond.ticker}</Td>
                  <Td>{bond.issuer_name}</Td>
                  <Td>{bond.credit_rating || 'NR'}</Td>
                  <Td>{bond.maturity_date}</Td>
                  <Td right mono>{(bond.coupon_rate * 100).toFixed(2)}%</Td>
                  <Td>{bond.sector}</Td>
                </tr>
              ))}
            </tbody>
          </TablePanel>
        </DataPanel>
      ) : <EmptyState message="No bonds found." />}
    </div>
  );
};
