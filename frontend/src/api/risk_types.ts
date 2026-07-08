export interface RiskLimitResponse {
  id: number;
  code: string;
  name: string;
  description?: string;
  metric_type: string;
  scope_type: string;
  scope_value?: string;
  direction: string;
  warning_threshold?: number;
  limit_threshold: number;
  severity: string;
  currency?: string;
  effective_from: string;
  effective_to?: string;
  is_active: boolean;
}

export interface LimitResultItem {
  metric_type: string;
  observed_value?: number;
  threshold_value: number;
  utilization_percent?: number;
  status: string;
  unit: string;
  calculation_source: string;
  model_status: string;
  limitations?: string;
}

export interface RiskEvaluationRun {
  id: number;
  portfolio_id: number;
  valuation_date: string;
  model_status: string;
  started_at: string;
  completed_at: string;
  overall_status: string;
  evaluated_limit_count: number;
  breach_count: number;
  warning_count: number;
  error_message?: string;
}

export interface ActiveBreachItem {
  breach_id: number;
  limit_code: string;
  metric_type: string;
  severity: string;
  status: string;
  observed_value: number;
  threshold_value: number;
  breach_amount: number;
  opened_at: string;
  acknowledged_at?: string;
  assigned_to?: string;
}

export interface RiskReportResponse {
  portfolio: any;
  report_metadata: any;
  portfolio_risk: any;
  market_risk: any;
  stress_risk: any;
  liquidity_risk: any;
  concentration: any;
  limit_summary: any;
  limit_results: LimitResultItem[];
  breach_summary: any;
  active_breaches: ActiveBreachItem[];
  model_governance: any;
}

export interface AuditEvent {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: number;
  action: string;
  actor: string;
  previous_state?: any;
  new_state?: any;
  metadata_json?: any;
  created_at: string;
}
