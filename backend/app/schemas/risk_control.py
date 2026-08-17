from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.risk_control.enums import LimitDirection, LimitSeverity, MetricType, ScopeType
from pydantic import BaseModel, ConfigDict


class RiskLimitCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    metric_type: MetricType
    scope_type: ScopeType
    scope_value: str | None = None
    direction: LimitDirection
    warning_threshold: Decimal | None = None
    limit_threshold: Decimal
    severity: LimitSeverity
    currency: str | None = None
    effective_from: date
    effective_to: date | None = None

class RiskLimitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    warning_threshold: Decimal | None = None
    limit_threshold: Decimal | None = None
    effective_to: date | None = None

class RiskLimitResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    metric_type: str
    scope_type: str
    scope_value: str | None
    direction: str
    warning_threshold: Decimal | None
    limit_threshold: Decimal
    severity: str
    currency: str | None
    effective_from: date
    effective_to: date | None
    is_active: bool


    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class ReportMetadata(BaseModel):
    valuation_date: date
    generated_at: datetime
    evaluation_run_id: int
    overall_status: str

class PortfolioRiskSection(BaseModel):
    total_market_value: float | None
    weighted_modified_duration: float | None
    total_dv01: float | None

class MarketRiskSection(BaseModel):
    historical_var: float | None
    parametric_var: float | None
    expected_shortfall: float | None
    model_status: str
    limitations: str | None

class StressRiskSection(BaseModel):
    worst_scenario_name: str | None
    worst_scenario_code: str | None
    pnl: float | None
    loss_percent: float | None

class LiquidityRiskSection(BaseModel):
    liquidity_score: float | None
    liquidation_cost: float | None
    liquidation_cost_bps: float | None
    weighted_days_to_liquidate: float | None
    max_days_to_liquidate: float | None
    model_label: str
    limitations: str | None

class ConcentrationSection(BaseModel):
    largest_issuer: str | None
    largest_issuer_weight: float | None
    largest_sector: str | None
    largest_sector_weight: float | None
    max_single_position_weight: float | None

class LimitSummary(BaseModel):
    evaluated_limit_count: int
    pass_count: int
    warning_count: int
    breach_count: int
    not_evaluated_count: int

class LimitResultItem(BaseModel):
    metric_type: str
    observed_value: Decimal | None
    threshold_value: Decimal
    utilization_percent: float | None
    status: str
    unit: str
    calculation_source: str
    model_status: str
    limitations: str | None

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
    acknowledged_at: datetime | None
    assigned_to: str | None

class ModelGovernance(BaseModel):
    active_models: list[str]
    degraded_models: list[str]
    proxy_models: list[str]
    limitations: list[str]

class RiskReportResponse(BaseModel):
    portfolio: dict[str, Any]
    report_metadata: ReportMetadata
    portfolio_risk: PortfolioRiskSection
    market_risk: MarketRiskSection
    stress_risk: StressRiskSection
    liquidity_risk: LiquidityRiskSection
    concentration: ConcentrationSection
    limit_summary: LimitSummary
    limit_results: list[LimitResultItem]
    breach_summary: BreachSummary
    active_breaches: list[ActiveBreachItem]
    model_governance: ModelGovernance

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})
