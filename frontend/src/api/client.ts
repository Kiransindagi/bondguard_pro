import axios from 'axios';
import type {
  RiskLimitResponse,
  RiskEvaluationRun,
  ActiveBreachItem,
  RiskReportResponse,
  AuditEvent
} from './risk_types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export const fetchSystemStatus = async () => {
  const response = await apiClient.get('/status');
  return response.data;
};

export const fetchDatabaseStatus = async () => {
  const response = await apiClient.get('/system/database');
  return response.data;
};

export const fetchDataStatus = async () => {
  const response = await apiClient.get('/market/data-status');
  return response.data;
};

export const fetchPortfolios = async () => {
  const response = await apiClient.get('/portfolios');
  return response.data;
};

export const fetchPortfolioSummary = async (portfolioId: number) => {
  const response = await apiClient.get(`/portfolios/${portfolioId}/summary`);
  return response.data;
};

export const fetchPortfolioPositions = async (portfolioId: number) => {
  const response = await apiClient.get(`/portfolios/${portfolioId}/positions`);
  return response.data;
};

export const fetchBonds = async (filters?: Record<string, string>) => {
  const params = new URLSearchParams(filters);
  const response = await apiClient.get(`/bonds?${params.toString()}`);
  return response.data;
};

export const fetchPortfolioRiskSummary = async (portfolioId: number) => {
  const response = await apiClient.get(`/risk/portfolios/${portfolioId}/summary`);
  return response.data;
};

export const fetchPortfolioPositionsRisk = async (portfolioId: number) => {
  const response = await apiClient.get(`/risk/portfolios/${portfolioId}/positions`);
  return response.data;
};


export const getYieldCurve = async (): Promise<any[]> => {
  const response = await apiClient.get('/market/yield-curve');
  return response.data;
};

export const getSpreads = async (spreadType?: string): Promise<any[]> => {
  let url = '/market/spreads';
  if (spreadType) {
    url += '?spread_type=' + encodeURIComponent(spreadType);
  }
  const response = await apiClient.get(url);
  return response.data;
};

// Risk Control extensions

export const evaluatePortfolioRiskControl = async (portfolioId: number): Promise<RiskEvaluationRun> => {
  const res = await apiClient.post(`/risk-control/portfolios/${portfolioId}/evaluate`);
  return res.data;
};

export const getLatestRiskEvaluation = async (portfolioId: number): Promise<{run: RiskEvaluationRun, results: any[]}> => {
  const res = await apiClient.get(`/risk-control/portfolios/${portfolioId}/latest`);
  return res.data;
};

export const getRiskEvaluationHistory = async (portfolioId: number): Promise<RiskEvaluationRun[]> => {
  const res = await apiClient.get(`/risk-control/portfolios/${portfolioId}/history`);
  return res.data;
};

export const getPortfolioBreaches = async (portfolioId: number): Promise<ActiveBreachItem[]> => {
  const res = await apiClient.get(`/risk-control/portfolios/${portfolioId}/breaches`);
  return res.data;
};

export const getBreach = async (breachId: number): Promise<ActiveBreachItem> => {
  const res = await apiClient.get(`/risk-control/breaches/${breachId}`);
  return res.data;
};

export const acknowledgeBreach = async (breachId: number, note?: string): Promise<any> => {
  let url = `/risk-control/breaches/${breachId}/acknowledge`;
  if (note) {
      url += `?note=${encodeURIComponent(note)}`;
  }
  const res = await apiClient.post(url);
  return res.data;
};

export const getAuditEvents = async (): Promise<AuditEvent[]> => {
  const res = await apiClient.get(`/risk-control/audit-events`);
  return res.data;
};

export const getRiskLimits = async (): Promise<RiskLimitResponse[]> => {
  const res = await apiClient.get(`/risk-control/limits`);
  return res.data;
};

export const createRiskLimit = async (limitData: Partial<RiskLimitResponse>): Promise<RiskLimitResponse> => {
  const res = await apiClient.post(`/risk-control/limits`, limitData);
  return res.data;
};

export const updateRiskLimit = async (limitId: number, limitData: Partial<RiskLimitResponse>): Promise<RiskLimitResponse> => {
  const res = await apiClient.patch(`/risk-control/limits/${limitId}`, limitData);
  return res.data;
};

export const deactivateRiskLimit = async (limitId: number): Promise<{message: string}> => {
  const res = await apiClient.delete(`/risk-control/limits/${limitId}`);
  return res.data;
};

export const getPortfolioRiskReport = async (portfolioId: number): Promise<RiskReportResponse> => {
  const res = await apiClient.get(`/risk-control/portfolios/${portfolioId}/report`);
  return res.data;
};

export const getSnapshots = async (portfolioId: number) => {
  const res = await apiClient.get(`/reporting/portfolios/${portfolioId}/snapshots`);
  return res.data;
};

export const getExecutiveReport = async (portfolioId: number) => {
  const res = await apiClient.get(`/reporting/portfolios/${portfolioId}/executive-report`);
  return res.data;
};

export const generateSnapshot = async (portfolioId: number) => {
  const res = await apiClient.post(`/reporting/portfolios/${portfolioId}/snapshots`);
  return res.data;
};

export const getFactorCorrelation = async (matrixType: string = 'production_factors') => {
  const res = await apiClient.get(`/market/factors/correlation?matrix_type=${matrixType}`);
  return res.data;
};
