import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader, DataPanel, TablePanel, Th, Td, Btn, LoadingState, ErrorState, EmptyState } from '../components/ui';
import { apiClient } from '../api/client';

export const AdminTransactions: React.FC = () => {
  const queryClient = useQueryClient();
  const [portfolioId, setPortfolioId] = useState<number | ''>('');
  const [bondId, setBondId] = useState<number | ''>('');
  const [transactionType, setTransactionType] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState('1000000'); // Face value units
  const [price, setPrice] = useState('100.00'); // Clean price (e.g. 100.00 is par)
  const [tradeDate, setTradeDate] = useState(new Date().toISOString().split('T')[0]);

  const { data: portfolios, isLoading: portsLoading } = useQuery<any[]>({
    queryKey: ['adminPortfoliosList'],
    queryFn: async () => (await apiClient.get('/portfolios')).data,
  });

  const { data: bonds, isLoading: bondsLoading } = useQuery<any[]>({
    queryKey: ['adminBondsList'],
    queryFn: async () => (await apiClient.get('/bonds')).data,
  });

  const { data: transactions, isLoading: txsLoading, isError, error } = useQuery<any[]>({
    queryKey: ['adminTransactions'],
    queryFn: async () => (await apiClient.get('/transactions')).data,
  });

  const executeMutation = useMutation({
    mutationFn: async (payload: any) => (await apiClient.post('/transactions', payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolioPositions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolioSummary'] });
      queryClient.invalidateQueries({ queryKey: ['latestAnalytics'] });
      queryClient.invalidateQueries({ queryKey: ['riskReport'] });
      resetForm();
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to execute transaction');
    }
  });

  const resetForm = () => {
    setBondId('');
    setQuantity('1000000');
    setPrice('100.00');
    setTradeDate(new Date().toISOString().split('T')[0]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!portfolioId || !bondId || !quantity || !price || !tradeDate) {
      alert('Please fill out all fields');
      return;
    }
    executeMutation.mutate({
      portfolio_id: Number(portfolioId),
      bond_id: Number(bondId),
      transaction_type: transactionType,
      quantity: parseFloat(quantity),
      price: parseFloat(price),
      trade_date: tradeDate,
    });
  };

  if (portsLoading || bondsLoading || txsLoading) return <LoadingState message="Loading Transactions Ledger..." />;
  if (isError) return <ErrorState message={`Error: ${String(error)}`} />;

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
    border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
    marginBottom: '12px'
  };

  const fmtQty = (v: any) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });

  return (
    <div>
      <PageHeader title="Transaction Ledger Administration" description="Execute buys/sells and audit transaction history across portfolios" />

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px', alignItems: 'start' }}>
        
        {/* Transaction Entry Form */}
        <DataPanel title="Record Transaction">
          <form onSubmit={handleSubmit}>
            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Portfolio</label>
              <select required value={portfolioId} onChange={e => setPortfolioId(Number(e.target.value))} style={inputStyle}>
                <option value="">-- Select Portfolio --</option>
                {portfolios?.filter(p => p.status === 'ACTIVE').map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Bond Security</label>
              <select required value={bondId} onChange={e => setBondId(Number(e.target.value))} style={inputStyle}>
                <option value="">-- Select Security --</option>
                {bonds?.map(b => (
                  <option key={b.id} value={b.id}>{b.isin} - {b.bond_name} ({b.issuer_name})</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Type</label>
                <select value={transactionType} onChange={e => setTransactionType(e.target.value as any)} style={inputStyle}>
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Trade Date</label>
                <input type="date" required value={tradeDate} onChange={e => setTradeDate(e.target.value)} style={inputStyle} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Quantity (Face Value)</label>
                <input type="number" required value={quantity} onChange={e => setQuantity(e.target.value)} style={inputStyle} placeholder="e.g. 1000000" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Clean Price</label>
                <input type="number" step="0.01" required value={price} onChange={e => setPrice(e.target.value)} style={inputStyle} placeholder="e.g. 100.00" />
              </div>
            </div>

            <div style={{ marginTop: '8px' }}>
              <Btn type="submit" variant="primary" style={{ width: '100%' }} disabled={executeMutation.isPending}>
                {executeMutation.isPending ? 'Executing Trade...' : 'Execute Trade'}
              </Btn>
            </div>
          </form>
        </DataPanel>

        {/* Transaction History Log */}
        <DataPanel title="Transaction History Audit Ledger">
          {transactions && transactions.length > 0 ? (
            <TablePanel>
              <thead>
                <tr>
                  <Th>ID</Th>
                  <Th>Trade Date</Th>
                  <Th>Portfolio</Th>
                  <Th>Security ISIN</Th>
                  <Th>Type</Th>
                  <Th right>Quantity (Face)</Th>
                  <Th right>Price</Th>
                </tr>
              </thead>
              <tbody>
                {transactions.map(tx => {
                  const portName = portfolios?.find(p => p.id === tx.portfolio_id)?.name || `Portfolio ${tx.portfolio_id}`;
                  const bondIsin = bonds?.find(b => b.id === tx.bond_id)?.isin || `Bond ${tx.bond_id}`;
                  const isBuy = tx.transaction_type === 'BUY';
                  return (
                    <tr key={tx.id}>
                      <Td mono>{tx.id}</Td>
                      <Td mono>{tx.trade_date}</Td>
                      <Td>{portName}</Td>
                      <Td mono style={{ fontSize: '11px' }}>{bondIsin}</Td>
                      <Td>
                        <span style={{
                          padding: '2px 6px', borderRadius: '4px',
                          backgroundColor: isBuy ? 'var(--bg-positive-subtle)' : 'var(--bg-critical-subtle)',
                          fontSize: '10px', fontWeight: 600,
                          color: isBuy ? 'var(--text-positive)' : 'var(--text-critical)'
                        }}>
                          {tx.transaction_type}
                        </span>
                      </Td>
                      <Td right mono>{fmtQty(tx.quantity)}</Td>
                      <Td right mono>{tx.price.toFixed(2)}</Td>
                    </tr>
                  );
                })}
              </tbody>
            </TablePanel>
          ) : <EmptyState message="No transactions recorded." />}
        </DataPanel>
      </div>
    </div>
  );
};
