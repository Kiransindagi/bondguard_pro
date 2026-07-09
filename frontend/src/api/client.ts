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

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Skip auth/login and auth/refresh from auto-refresh to avoid loops
    if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = 'Bearer ' + token;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        originalRequest.headers.Authorization = 'Bearer ' + access_token;
        processQueue(null, access_token);
        isRefreshing = false;
        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        isRefreshing = false;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Dispatch custom event to notify app of logout / session expiry
        window.dispatchEvent(new Event('auth-session-expired'));
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  }
);

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

// Sprint 9 Operational Layer endpoints
export const fetchOperationalHealth = async () => {
  const response = await apiClient.get('/system/health');
  return response.data;
};

export const triggerPipelineRun = async (params: { run_type?: string; dataset_key?: string; category?: string; start_date?: string; end_date?: string } = {}) => {
  const response = await apiClient.post('/data-pipeline/run', params);
  return response.data;
};

export const getPipelineRuns = async () => {
  const response = await apiClient.get('/data-pipeline/runs');
  return response.data;
};

export const getPipelineRun = async (runId: number) => {
  const response = await apiClient.get(`/data-pipeline/runs/${runId}`);
  return response.data;
};

export const triggerDataQualityRun = async () => {
  const response = await apiClient.post('/data-quality/run');
  return response.data;
};

export const getLatestQualitySummary = async () => {
  const response = await apiClient.get('/data-quality/summary');
  return response.data;
};

export const getDatasetQualityStatus = async () => {
  const response = await apiClient.get('/data-quality/datasets');
  return response.data;
};

export const getDatasetQualityDetails = async (datasetKey: string) => {
  const response = await apiClient.get(`/data-quality/datasets/${datasetKey}`);
  return response.data;
};

export const triggerAnalyticsRun = async (portfolioId: number, valuationDate?: string) => {
  const response = await apiClient.post(`/analytics/portfolios/${portfolioId}/run`, { valuation_date: valuationDate });
  return response.data;
};

export const getLatestAnalytics = async (portfolioId: number) => {
  const response = await apiClient.get(`/analytics/portfolios/${portfolioId}/latest`);
  return response.data;
};

export const getAnalyticsHistory = async (portfolioId: number) => {
  const response = await apiClient.get(`/analytics/portfolios/${portfolioId}/history`);
  return response.data;
};

export const getAnalyticsRun = async (runId: number) => {
  const response = await apiClient.get(`/analytics/runs/${runId}`);
  return response.data;
};

// --- Sprint 11: Notifications ---
export const getNotifications = async () => {
  const response = await apiClient.get('/notifications');
  return response.data;
};

export const getUnreadNotificationsCount = async () => {
  const response = await apiClient.get('/notifications/unread-count');
  return response.data;
};

export const markNotificationRead = async (id: number) => {
  const response = await apiClient.post(`/notifications/${id}/read`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  const response = await apiClient.post('/notifications/read-all');
  return response.data;
};

// --- Sprint 11: Breach Workflow ---
export const getBreachWorkflow = async (id: number) => {
  const response = await apiClient.get(`/risk-control/breaches/${id}/workflow`);
  return response.data;
};

export const assignBreach = async (id: number, userId: number) => {
  const response = await apiClient.post(`/risk-control/breaches/${id}/assign`, null, { params: { user_id: userId } });
  return response.data;
};

export const reviewBreach = async (id: number, notes: string) => {
  const response = await apiClient.post(`/risk-control/breaches/${id}/review`, null, { params: { notes } });
  return response.data;
};

export const resolveBreach = async (id: number, notes: string) => {
  const response = await apiClient.post(`/risk-control/breaches/${id}/resolve`, null, { params: { notes } });
  return response.data;
};

export const getAssignableUsers = async () => {
  const response = await apiClient.get('/risk-control/assignable-users');
  return response.data;
};

// --- Sprint 11: Scenario Lab ---
export const runCustomScenario = async (req: any) => {
  const response = await apiClient.post('/scenario-lab/run', req);
  return response.data;
};

export const createSavedScenario = async (scen: any) => {
  const response = await apiClient.post('/scenario-lab/scenarios', scen);
  return response.data;
};

export const getSavedScenarios = async () => {
  const response = await apiClient.get('/scenario-lab/scenarios');
  return response.data;
};

export const getSavedScenario = async (id: number) => {
  const response = await apiClient.get(`/scenario-lab/scenarios/${id}`);
  return response.data;
};

export const updateSavedScenario = async (id: number, scen: any) => {
  const response = await apiClient.put(`/scenario-lab/scenarios/${id}`, scen);
  return response.data;
};

export const deleteSavedScenario = async (id: number) => {
  const response = await apiClient.delete(`/scenario-lab/scenarios/${id}`);
  return response.data;
};

export const comparePortfolioScenario = async (portfolioId: number, scenarioId: number, valuationDate?: string) => {
  const response = await apiClient.post(`/scenario-lab/portfolios/${portfolioId}/compare`, null, {
    params: { scenario_id: scenarioId, valuation_date: valuationDate }
  });
  return response.data;
};

// --- Sprint 11: Advanced Analytics ---
export const getBondKeyRateDuration = async (bondId: number, valuationDate?: string, cleanPrice?: number) => {
  const response = await apiClient.get(`/advanced-risk/bonds/${bondId}/key-rate-duration`, {
    params: { valuation_date: valuationDate, clean_price: cleanPrice }
  });
  return response.data;
};

export const getPortfolioKeyRateDuration = async (portfolioId: number, valuationDate?: string) => {
  const response = await apiClient.get(`/advanced-risk/portfolios/${portfolioId}/key-rate-duration`, {
    params: { valuation_date: valuationDate }
  });
  return response.data;
};

export const getPortfolioBucketedDV01 = async (portfolioId: number, valuationDate?: string) => {
  const response = await apiClient.get(`/advanced-risk/portfolios/${portfolioId}/bucketed-dv01`, {
    params: { valuation_date: valuationDate }
  });
  return response.data;
};

export const getPortfolioSpreadRisk = async (portfolioId: number, valuationDate?: string) => {
  const response = await apiClient.get(`/advanced-risk/portfolios/${portfolioId}/spread-risk`, {
    params: { valuation_date: valuationDate }
  });
  return response.data;
};

export const getPortfolioCarryRollDown = async (portfolioId: number, valuationDate?: string, horizonMonths: number = 1) => {
  const response = await apiClient.get(`/advanced-risk/portfolios/${portfolioId}/carry-roll-down`, {
    params: { valuation_date: valuationDate, horizon_months: horizonMonths }
  });
  return response.data;
};

export const getPortfolioPnLExplain = async (portfolioId: number, rateShockBps: number, spreadShockBps: number, actualPnL: number, valuationDate?: string) => {
  const response = await apiClient.get(`/advanced-risk/portfolios/${portfolioId}/pnl-explain`, {
    params: { rate_shock_bps: rateShockBps, spread_shock_bps: spreadShockBps, actual_pnl: actualPnL, valuation_date: valuationDate }
  });
  return response.data;
};
