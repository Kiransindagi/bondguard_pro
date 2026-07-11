import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader, DataPanel, TablePanel, Th, Td, Btn, LoadingState, ErrorState, EmptyState } from '../components/ui';
import { apiClient } from '../api/client';

export const AdminPortfolios: React.FC = () => {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('USD');
  const [benchmark, setBenchmark] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);

  const { data: portfolios, isLoading, isError, error } = useQuery<any[]>({
    queryKey: ['adminPortfolios'],
    queryFn: async () => (await apiClient.get('/portfolios')).data,
  });

  const createMutation = useMutation({
    mutationFn: async (payload: any) => (await apiClient.post('/portfolios', payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPortfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: any }) => 
      (await apiClient.patch(`/portfolios/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPortfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => (await apiClient.delete(`/portfolios/${id}`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPortfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });

  const resetForm = () => {
    setName('');
    setDescription('');
    setBaseCurrency('USD');
    setBenchmark('');
    setEditingId(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    const payload = { name, description, base_currency: baseCurrency, benchmark };
    if (editingId) {
      updateMutation.mutate({ id: editingId, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleEdit = (port: any) => {
    setEditingId(port.id);
    setName(port.name);
    setDescription(port.description || '');
    setBaseCurrency(port.base_currency);
    setBenchmark(port.benchmark || '');
  };

  const handleToggleActive = (port: any) => {
    updateMutation.mutate({
      id: port.id,
      payload: { is_active: !port.is_active }
    });
  };

  const handleArchive = (id: number) => {
    if (confirm('Are you sure you want to archive this portfolio? This cannot be undone.')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) return <LoadingState message="Loading Portfolio Administration..." />;
  if (isError) return <ErrorState message={`Error: ${String(error)}`} />;

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--bg-inset)', color: 'var(--text-primary)',
    border: '1px solid var(--border-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px',
    marginBottom: '12px'
  };

  return (
    <div>
      <PageHeader title="Portfolio Administration" description="Manage configurations and operational lifecycles for fixed income portfolios" />

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
        
        {/* Form Panel */}
        <DataPanel title={editingId ? 'Edit Portfolio' : 'Create Portfolio'}>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '8px' }}>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Portfolio Name</label>
              <input type="text" required value={name} onChange={e => setName(e.target.value)} style={inputStyle} placeholder="e.g. Core Fixed Income" />
            </div>

            <div style={{ marginBottom: '8px' }}>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Description</label>
              <textarea value={description} onChange={e => setDescription(e.target.value)} style={{ ...inputStyle, minHeight: '60px', resize: 'vertical' }} placeholder="Optional details..." />
            </div>

            <div style={{ marginBottom: '8px' }}>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Base Currency</label>
              <select value={baseCurrency} onChange={e => setBaseCurrency(e.target.value)} style={inputStyle}>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Benchmark</label>
              <input type="text" value={benchmark} onChange={e => setBenchmark(e.target.value)} style={inputStyle} placeholder="e.g. Bloomberg US Aggregate" />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Btn type="submit" variant="primary" style={{ flex: 1 }}>{editingId ? 'Save Changes' : 'Create Portfolio'}</Btn>
              {editingId && <Btn type="button" onClick={resetForm} variant="ghost">Cancel</Btn>}
            </div>
          </form>
        </DataPanel>

        {/* List Panel */}
        <DataPanel title="All Portfolios">
          {portfolios && portfolios.length > 0 ? (
            <TablePanel>
              <thead>
                <tr>
                  <Th>ID</Th>
                  <Th>Name</Th>
                  <Th>Currency</Th>
                  <Th>Benchmark</Th>
                  <Th>Status</Th>
                  <Th right>Actions</Th>
                </tr>
              </thead>
              <tbody>
                {portfolios.map(port => (
                  <tr key={port.id} style={{ opacity: port.status === 'ARCHIVED' ? 0.5 : 1 }}>
                    <Td mono>{port.id}</Td>
                    <Td>
                      <div style={{ fontWeight: 500 }}>{port.name}</div>
                      {port.description && <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{port.description}</div>}
                    </Td>
                    <Td mono>{port.base_currency}</Td>
                    <Td>{port.benchmark || 'None'}</Td>
                    <Td>
                      <span style={{ marginRight: '8px' }}>
                        <Btn variant="ghost" size="sm" onClick={() => handleToggleActive(port)} disabled={port.status === 'ARCHIVED'}>
                          {port.is_active ? 'Active' : 'Inactive'}
                        </Btn>
                      </span>
                      <span style={{ fontSize: '10px', color: port.status === 'ACTIVE' ? 'var(--text-positive)' : 'var(--text-critical)', fontWeight: 600, textTransform: 'uppercase' }}>
                        {port.status}
                      </span>
                    </Td>
                    <Td right>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <Btn variant="ghost" size="sm" onClick={() => handleEdit(port)} disabled={port.status === 'ARCHIVED'}>Edit</Btn>
                        <Btn variant="danger" size="sm" onClick={() => handleArchive(port.id)} disabled={port.status === 'ARCHIVED'}>Archive</Btn>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TablePanel>
          ) : <EmptyState message="No portfolios found." />}
        </DataPanel>
      </div>
    </div>
  );
};
