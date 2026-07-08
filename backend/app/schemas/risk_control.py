from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from app.risk_control.enums import MetricType, ScopeType, LimitDirection, LimitSeverity

class RiskLimitCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    metric_type: MetricType
    scope_type: ScopeType
    scope_value: Optional[str] = None
    direction: LimitDirection
    warning_threshold: Optional[Decimal] = None
    limit_threshold: Decimal
    severity: LimitSeverity
    currency: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None

class RiskLimitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    warning_threshold: Optional[Decimal] = None
    limit_threshold: Optional[Decimal] = None
    effective_to: Optional[date] = None

class RiskLimitResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    metric_type: str
    scope_type: str
    scope_value: Optional[str]
    direction: str
    warning_threshold: Optional[Decimal]
    limit_threshold: Decimal
    severity: str
    currency: Optional[str]
    effective_from: date
    effective_to: Optional[date]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ReportMetadata(BaseModel):
    valuation_date: date
    generated_at: datetime
    evaluation_run_id: int
    overall_status: str

class PortfolioRiskSection(BaseModel):
    total_market_value: Optional[Decimal]
    weighted_modified_duration: Optional[Decimal]
    total_dv01: Optional[Decimal]

class MarketRiskSection(BaseModel):
    historical_var: Optional[Decimal]
    parametric_var: Optional[Decimal]
    expected_shortfall: Optional[Decimal]
    model_status: str
    limitations: Optional[str]

class StressRiskSection(BaseModel):
    worst_scenario_name: Optional[str]
    worst_scenario_code: Optional[str]
    pnl: Optional[Decimal]
    loss_percent: Optional[Decimal]

class LiquidityRiskSection(BaseModel):
    liquidity_score: Optional[Decimal]
    liquidation_cost: Optional[Decimal]
    liquidation_cost_bps: Optional[Decimal]
    weighted_days_to_liquidate: Optional[Decimal]
    max_days_to_liquidate: Optional[Decimal]
    model_label: str
    limitations: Optional[str]

class ConcentrationSection(BaseModel):
    largest_issuer: Optional[str]
    largest_issuer_weight: Optional[Decimal]
    largest_sector: Optional[str]
    largest_sector_weight: Optional[Decimal]
    max_single_position_weight: Optional[Decimal]

class LimitSummary(BaseModel):
    evaluated_limit_count: int
    pass_count: int
    warning_count: int
    breach_count: int
    not_evaluated_count: int

class LimitResultItem(BaseModel):
    metric_type: str
    observed_value: Optional[Decimal]
    threshold_value: Decimal
    utilization_percent: Optional[float]
    status: str
    unit: str
    calculation_source: str
    model_status: str
    limitations: Optional[str]

class BreachSummary(BaseModel):
    open_count: int
    acknowledged_count: int
    resolved_count: int

class ActiveBreachItem(BaseModel):
    breach_id: int
    limit_code: str
    metric_type: str
    severity: str
    status: str
    observed_value: Decimal
    threshold_value: Decimal
    breach_amount: Decimal
    opened_at: datetime
    acknowledged_at: Optional[datetime]
    assigned_to: Optional[str]

class ModelGovernance(BaseModel):
    active_models: List[str]
    degraded_models: List[str]
    proxy_models: List[str]
    limitations: List[str]

class RiskReportResponse(BaseModel):
    portfolio: Dict[str, Any]
    report_metadata: ReportMetadata
    portfolio_risk: PortfolioRiskSection
    market_risk: MarketRiskSection
    stress_risk: StressRiskSection
    liquidity_risk: LiquidityRiskSection
    concentration: ConcentrationSection
    limit_summary: LimitSummary
    limit_results: List[LimitResultItem]
    breach_summary: BreachSummary
    active_breaches: List[ActiveBreachItem]
    model_governance: ModelGovernance

    model_config = ConfigDict(from_attributes=True)
