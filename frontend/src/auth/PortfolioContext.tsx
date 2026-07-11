import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPortfolios } from '../api/client';

export interface PortfolioType {
  id: number;
  name: string;
  description?: string;
  base_currency: string;
  benchmark?: string;
  is_active: boolean;
  status: string;
}

interface PortfolioContextType {
  selectedPortfolioId: number | null;
  selectedPortfolio: PortfolioType | null;
  portfolios: PortfolioType[] | null;
  loading: boolean;
  selectPortfolio: (id: number) => void;
  refetchPortfolios: () => void;
}

const PortfolioContext = createContext<PortfolioContextType | null>(null);

export const PortfolioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: portfolios, isLoading, refetch } = useQuery({
    queryKey: ['portfolios'],
    queryFn: fetchPortfolios,
  });

  useEffect(() => {
    if (portfolios && portfolios.length > 0) {
      const saved = localStorage.getItem('selected_portfolio_id');
      const savedId = saved ? parseInt(saved, 10) : null;
      if (savedId && portfolios.some((p: PortfolioType) => p.id === savedId)) {
        setSelectedId(savedId);
      } else {
        setSelectedId(portfolios[0].id);
        localStorage.setItem('selected_portfolio_id', String(portfolios[0].id));
      }
    } else {
      setSelectedId(null);
    }
  }, [portfolios]);

  const selectPortfolio = (id: number) => {
    if (portfolios && portfolios.some((p: PortfolioType) => p.id === id)) {
      setSelectedId(id);
      localStorage.setItem('selected_portfolio_id', String(id));
    }
  };

  const selectedPortfolio = portfolios?.find((p: PortfolioType) => p.id === selectedId) || null;

  return (
    <PortfolioContext.Provider value={{
      selectedPortfolioId: selectedId,
      selectedPortfolio,
      portfolios: portfolios || null,
      loading: isLoading,
      selectPortfolio,
      refetchPortfolios: refetch,
    }}>
      {children}
    </PortfolioContext.Provider>
  );
};

export const usePortfolio = () => {
  const context = useContext(PortfolioContext);
  if (!context) {
    throw new Error('usePortfolio must be used within a PortfolioProvider');
  }
  return context;
};
