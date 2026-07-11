import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader, DataPanel, TablePanel, Th, Td, Btn, LoadingState, ErrorState, EmptyState } from '../components/ui';
import { apiClient } from '../api/client';

export const AdminBonds: React.FC = () => {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form state fields
  const [isin, setIsin] = useState('');
  const [cusip, setCusip] = useState('');
  const [ticker, setTicker] = useState('');
  const [issuerName, setIssuerName] = useState('');
  const [bondName, setBondName] = useState('');
  const [faceValue, setFaceValue] = useState('1000');
  const [couponRate, setCouponRate] = useState('0.05');
  const [couponFrequency, setCouponFrequency] = useState('semiannual');
  const [issueDate, setIssueDate] = useState('');
  const [maturityDate, setMaturityDate] = useState('');
  const [dayCountConvention, setDayCountConvention] = useState('30/360');
  const [bondType, setBondType] = useState('CORPORATE');
  const [creditRating, setCreditRating] = useState('BBB');
  const [sector, setSector] = useState('Financials');
  const [country, setCountry] = useState('US');

  const { data: bonds, isLoading, isError, error } = useQuery<any[]>({
    queryKey: ['adminBonds'],
    queryFn: async () => (await apiClient.get('/bonds')).data,
  });

  const createMutation = useMutation({
    mutationFn: async (payload: any) => (await apiClient.post('/bonds', payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBonds'] });
      resetForm();
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to create bond');
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: any }) => 
      (await apiClient.patch(`/bonds/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBonds'] });
      resetForm();
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to update bond');
    }
  });

  const resetForm = () => {
    setEditingId(null);
    setIsin('');
    setCusip('');
    setTicker('');
    setIssuerName('');
    setBondName('');
    setFaceValue('1000');
    setCouponRate('0.05');
    setCouponFrequency('semiannual');
    setIssueDate('');
    setMaturityDate('');
    setDayCountConvention('30/360');
    setBondType('CORPORATE');
    setCreditRating('BBB');
    setSector('Financials');
    setCountry('US');
  };

  const handleEdit = (bond: any) => {
    setEditingId(bond.id);
    setIsin(bond.isin);
    setCusip(bond.cusip || '');
    setTicker(bond.ticker || '');
    setIssuerName(bond.issuer_name);
    setBondName(bond.bond_name);
    setFaceValue(String(bond.face_value));
    setCouponRate(String(bond.coupon_rate));
    setCouponFrequency(bond.coupon_frequency);
    setIssueDate(bond.issue_date);
    setMaturityDate(bond.maturity_date);
    setDayCountConvention(bond.day_count_convention);
    setBondType(bond.bond_type);
    setCreditRating(bond.credit_rating || '');
    setSector(bond.sector || '');
    setCountry(bond.country || '');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      // Only allow editing metadata parameters: issuer_name, bond_name, credit_rating, sector, country
      updateMutation.mutate({
        id: editingId,
        payload: {
          issuer_name: issuerName,
          bond_name: bondName,
          credit_rating: creditRating,
          sector,
          country,
        }
      });
    } else {
      createMutation.mutate({
        isin,
        cusip: cusip || null,
        ticker: ticker || null,
        issuer_name: issuerName,
        bond_name: bondName,
        face_value: parseFloat(faceValue),
        coupon_rate: parseFloat(couponRate),
        coupon_frequency: couponFrequency,
        issue_date: issueDate,
        maturity_date: maturityDate,
        day_count_convention: dayCountConvention,
        bond_type: bondType,
        credit_rating: creditRating || null,
        sector: sector || null,
        country: country || null,
      });
    }
  };

  if (isLoading) return <LoadingState message="Loading Securities Master..." />;
  if (isError) return <ErrorState message={`Error: ${String(error)}`} />;

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '6px 10px', borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
    border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
    marginBottom: '8px'
  };

  return (
    <div>
      <PageHeader title="Securities Master Administration" description="Manage bond reference database and master characteristics" />

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px', alignItems: 'start' }}>
        
        {/* Creation/Edit Form */}
        <DataPanel title={editingId ? 'Edit Bond Reference' : 'Register New Bond'}>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>ISIN</label>
                <input type="text" required disabled={!!editingId} value={isin} onChange={e => setIsin(e.target.value)} style={inputStyle} placeholder="e.g. US912828GD97" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>CUSIP</label>
                <input type="text" disabled={!!editingId} value={cusip} onChange={e => setCusip(e.target.value)} style={inputStyle} placeholder="e.g. 912828GD9" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Ticker</label>
                <input type="text" disabled={!!editingId} value={ticker} onChange={e => setTicker(e.target.value)} style={inputStyle} placeholder="e.g. T 3.125" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Bond Type</label>
                <input type="text" disabled={!!editingId} value={bondType} onChange={e => setBondType(e.target.value)} style={inputStyle} placeholder="CORPORATE / GOVT" />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Issuer Name</label>
              <input type="text" required value={issuerName} onChange={e => setIssuerName(e.target.value)} style={inputStyle} />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Bond Name</label>
              <input type="text" required value={bondName} onChange={e => setBondName(e.target.value)} style={inputStyle} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Face Value</label>
                <input type="number" required disabled={!!editingId} value={faceValue} onChange={e => setFaceValue(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Coupon Rate</label>
                <input type="number" step="0.0001" required disabled={!!editingId} value={couponRate} onChange={e => setCouponRate(e.target.value)} style={inputStyle} placeholder="0.05 for 5%" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Coupon Freq</label>
                <select disabled={!!editingId} value={couponFrequency} onChange={e => setCouponFrequency(e.target.value)} style={inputStyle}>
                  <option value="annual">Annual</option>
                  <option value="semiannual">Semiannual</option>
                  <option value="quarterly">Quarterly</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Day Count</label>
                <select disabled={!!editingId} value={dayCountConvention} onChange={e => setDayCountConvention(e.target.value)} style={inputStyle}>
                  <option value="ACT/ACT">ACT/ACT</option>
                  <option value="30/360">30/360</option>
                  <option value="ACT/360">ACT/360</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Issue Date</label>
                <input type="date" required disabled={!!editingId} value={issueDate} onChange={e => setIssueDate(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Maturity Date</label>
                <input type="date" required disabled={!!editingId} value={maturityDate} onChange={e => setMaturityDate(e.target.value)} style={inputStyle} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Rating</label>
                <input type="text" value={creditRating} onChange={e => setCreditRating(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Sector</label>
                <input type="text" value={sector} onChange={e => setSector(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '3px', textTransform: 'uppercase' }}>Country</label>
                <input type="text" value={country} onChange={e => setCountry(e.target.value)} style={inputStyle} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Btn type="submit" variant="primary" style={{ flex: 1 }}>{editingId ? 'Save Changes' : 'Register Bond'}</Btn>
              <Btn type="button" onClick={resetForm} variant="ghost">Cancel</Btn>
            </div>
          </form>
        </DataPanel>

        {/* Bonds Master List */}
        <DataPanel title="Securities Reference Data">
          {bonds && bonds.length > 0 ? (
            <TablePanel>
              <thead>
                <tr>
                  <Th>ID</Th>
                  <Th>ISIN / CUSIP</Th>
                  <Th>Name / Issuer</Th>
                  <Th>Coupon / Freq</Th>
                  <Th>Maturity</Th>
                  <Th>Rating / Sector</Th>
                  <Th right>Actions</Th>
                </tr>
              </thead>
              <tbody>
                {bonds.map(bond => (
                  <tr key={bond.id}>
                    <Td mono>{bond.id}</Td>
                    <Td>
                      <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{bond.isin}</div>
                      {bond.cusip && <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{bond.cusip}</div>}
                    </Td>
                    <Td>
                      <div style={{ fontWeight: 500 }}>{bond.bond_name}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{bond.issuer_name} ({bond.country})</div>
                    </Td>
                    <Td mono>
                      {(bond.coupon_rate * 100).toFixed(3)}%
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{bond.coupon_frequency}</div>
                    </Td>
                    <Td mono>{bond.maturity_date}</Td>
                    <Td>
                      <span style={{
                        padding: '2px 6px', borderRadius: '4px',
                        backgroundColor: 'var(--bg-inset)', fontSize: '10px',
                        fontWeight: 600, color: 'var(--text-accent)', marginRight: '6px'
                      }}>{bond.credit_rating || 'NR'}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{bond.sector || 'Unassigned'}</span>
                    </Td>
                    <Td right>
                      <Btn variant="ghost" size="sm" onClick={() => handleEdit(bond)}>Edit Reference</Btn>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TablePanel>
          ) : <EmptyState message="No bonds in Security Master database." />}
        </DataPanel>
      </div>
    </div>
  );
};
