import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBonds } from '../api/client';

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
      <h1 style={{ fontSize: '2rem', color: '#e2e8f0', marginBottom: '1rem' }}>Bond Explorer</h1>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <input 
          type="text" 
          placeholder="Filter by Issuer..." 
          value={issuer} 
          onChange={(e) => setIssuer(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#e2e8f0' }}
        />
        <input 
          type="text" 
          placeholder="Filter by Rating..." 
          value={rating} 
          onChange={(e) => setRating(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#e2e8f0' }}
        />
        <input 
          type="text" 
          placeholder="Filter by Sector..." 
          value={sector} 
          onChange={(e) => setSector(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#e2e8f0' }}
        />
      </div>

      {isLoading ? (
        <p style={{ color: '#94a3b8' }}>Loading bonds...</p>
      ) : isError ? (
        <p style={{ color: '#ef4444' }}>Error loading bonds.</p>
      ) : bonds && bonds.length > 0 ? (
        <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '0.75rem' }}>ISIN</th>
                <th style={{ padding: '0.75rem' }}>Ticker</th>
                <th style={{ padding: '0.75rem' }}>Issuer</th>
                <th style={{ padding: '0.75rem' }}>Rating</th>
                <th style={{ padding: '0.75rem' }}>Maturity</th>
                <th style={{ padding: '0.75rem' }}>Coupon</th>
                <th style={{ padding: '0.75rem' }}>Sector</th>
              </tr>
            </thead>
            <tbody>
              {bonds.map((bond: any) => (
                <tr key={bond.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '0.75rem' }}>{bond.isin}</td>
                  <td style={{ padding: '0.75rem' }}>{bond.ticker}</td>
                  <td style={{ padding: '0.75rem' }}>{bond.issuer_name}</td>
                  <td style={{ padding: '0.75rem' }}>{bond.credit_rating || 'NR'}</td>
                  <td style={{ padding: '0.75rem' }}>{bond.maturity_date}</td>
                  <td style={{ padding: '0.75rem' }}>{(bond.coupon_rate * 100).toFixed(2)}%</td>
                  <td style={{ padding: '0.75rem' }}>{bond.sector}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ color: '#94a3b8' }}>No bonds found.</p>
      )}
    </div>
  );
};
