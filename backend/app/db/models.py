from app.db.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class SystemMetadata(Base):
    __tablename__ = "system_metadata"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    instrument_type = Column(String, nullable=False)
    asset_class = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = (UniqueConstraint('instrument_id', 'observation_date', 'source', name='uq_market_price_obs'),)

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    observation_date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class YieldCurvePoint(Base):
    __tablename__ = "yield_curve_points"
    __table_args__ = (UniqueConstraint('observation_date', 'tenor_years', 'source', name='uq_yield_curve_obs'),)

    id = Column(Integer, primary_key=True, index=True)
    observation_date = Column(Date, nullable=False)
    tenor_years = Column(Float, nullable=False)
    yield_percent = Column(Float, nullable=False)
    series_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class CreditSpread(Base):
    __tablename__ = "credit_spreads"
    __table_args__ = (UniqueConstraint('observation_date', 'spread_type', 'source', name='uq_credit_spread_obs'),)

    id = Column(Integer, primary_key=True, index=True)
    observation_date = Column(Date, nullable=False)
    spread_type = Column(String, nullable=False)
    spread_bps = Column(Float, nullable=False)
    series_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class MacroObservation(Base):
    __tablename__ = "macro_observations"
    __table_args__ = (UniqueConstraint('observation_date', 'series_id', name='uq_macro_obs'),)

    id = Column(Integer, primary_key=True, index=True)
    observation_date = Column(Date, nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    series_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class DataIngestionRun(Base):
    __tablename__ = "data_ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)  # RUNNING, SUCCESS, PARTIAL, FAILED
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    base_currency = Column(String, nullable=False, default="USD")
    benchmark = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    positions = relationship("Position", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")

class Bond(Base):
    __tablename__ = "bonds"
    id = Column(Integer, primary_key=True, index=True)
    isin = Column(String, unique=True, index=True, nullable=False)
    cusip = Column(String, unique=True, index=True, nullable=True)
    ticker = Column(String, index=True, nullable=True)
    issuer_name = Column(String, nullable=False)
    bond_name = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    face_value = Column(Numeric(18, 2), nullable=False)
    coupon_rate = Column(Numeric(8, 6), nullable=False)
    coupon_frequency = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    day_count_convention = Column(String, nullable=False)
    bond_type = Column(String, nullable=False)
    credit_rating = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    positions = relationship("Position", back_populates="bond")
    transactions = relationship("Transaction", back_populates="bond")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    bond_id = Column(Integer, ForeignKey("bonds.id"), nullable=False)
    transaction_type = Column(String, nullable=False) # BUY or SELL
    trade_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False)
    clean_price = Column(Numeric(18, 6), nullable=False)
    accrued_interest = Column(Numeric(18, 6), nullable=False, default=0.0)
    total_consideration = Column(Numeric(18, 6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="transactions")
    bond = relationship("Bond", back_populates="transactions")

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint('portfolio_id', 'bond_id', name='uq_portfolio_bond_position'),)
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    bond_id = Column(Integer, ForeignKey("bonds.id"), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False, default=0)
    average_cost = Column(Numeric(18, 6), nullable=False, default=0)
    current_clean_price = Column(Numeric(18, 6), nullable=True)
    market_value = Column(Numeric(18, 6), nullable=True)
    unrealized_pnl = Column(Numeric(18, 6), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    portfolio = relationship("Portfolio", back_populates="positions")
    bond = relationship("Bond", back_populates="positions")


class StressScenario(Base):
    __tablename__ = 'stress_scenarios'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    scenario_type = Column(String, nullable=False)
    is_predefined = Column(Boolean, default=False)
    rate_2y_shock_bps = Column(Float, nullable=False, default=0.0)
    rate_5y_shock_bps = Column(Float, nullable=False, default=0.0)
    rate_10y_shock_bps = Column(Float, nullable=False, default=0.0)
    rate_30y_shock_bps = Column(Float, nullable=False, default=0.0)
    ig_spread_shock_bps = Column(Float, nullable=False, default=0.0)
    hy_spread_shock_bps = Column(Float, nullable=False, default=0.0)
    default_calculation_method = Column(String, nullable=False, default='FULL_REVALUATION')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class StressTestRun(Base):
    __tablename__ = 'stress_test_runs'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    scenario_id = Column(Integer, ForeignKey('stress_scenarios.id'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    calculation_method = Column(String, nullable=False)
    base_market_value = Column(Numeric(18, 6), nullable=False)
    stressed_market_value = Column(Numeric(18, 6), nullable=False)
    total_pnl = Column(Numeric(18, 6), nullable=False)
    total_loss_percent = Column(Float, nullable=False)
    position_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StressPositionResult(Base):
    __tablename__ = 'stress_position_results'

    id = Column(Integer, primary_key=True, index=True)
    stress_test_run_id = Column(Integer, ForeignKey('stress_test_runs.id'), nullable=False)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)
    bond_id = Column(Integer, ForeignKey('bonds.id'), nullable=False)
    base_clean_price = Column(Numeric(18, 6), nullable=False)
    stressed_clean_price = Column(Numeric(18, 6), nullable=False)
    base_market_value = Column(Numeric(18, 6), nullable=False)
    stressed_market_value = Column(Numeric(18, 6), nullable=False)
    pnl = Column(Numeric(18, 6), nullable=False)
    pnl_percent = Column(Float, nullable=False)
    rate_shock_bps = Column(Float, nullable=False)
    spread_shock_bps = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiquidityAssumption(Base):
    __tablename__ = 'liquidity_assumptions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String, nullable=True)
    methodology = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    configuration_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LiquiditySnapshot(Base):
    __tablename__ = 'liquidity_snapshots'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    assumption_id = Column(Integer, ForeignKey('liquidity_assumptions.id'), nullable=False)

    portfolio_market_value = Column(Numeric(18, 6), nullable=False)
    weighted_liquidity_score = Column(Float, nullable=False)
    estimated_liquidation_cost = Column(Numeric(18, 6), nullable=False)
    estimated_liquidation_cost_bps = Column(Float, nullable=False)
    weighted_days_to_liquidate = Column(Float, nullable=False)
    max_days_to_liquidate = Column(Integer, nullable=False)
    very_low_liquidity_market_value = Column(Numeric(18, 6), nullable=False)
    very_low_liquidity_weight = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LiquidityPositionResult(Base):
    __tablename__ = 'liquidity_position_results'

    id = Column(Integer, primary_key=True, index=True)
    liquidity_snapshot_id = Column(Integer, ForeignKey('liquidity_snapshots.id'), nullable=False)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)
    bond_id = Column(Integer, ForeignKey('bonds.id'), nullable=False)

    market_value = Column(Numeric(18, 6), nullable=False)
    liquidity_score = Column(Float, nullable=False)
    liquidity_class = Column(String, nullable=False)

    estimated_bid_ask_bps = Column(Float, nullable=False)
    estimated_liquidation_cost = Column(Numeric(18, 6), nullable=False)

    model_daily_capacity = Column(Numeric(18, 6), nullable=False)
    participation_rate = Column(Float, nullable=False)

    raw_days_to_liquidate = Column(Float, nullable=False)
    estimated_trading_days_to_liquidate = Column(Integer, nullable=False)
    liquidation_horizon_bucket = Column(String, nullable=False)

    source_type = Column(String, nullable=False)
    methodology = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConcentrationLimit(Base):
    __tablename__ = 'concentration_limits'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)
    limit_type = Column(String, nullable=False)
    threshold_value = Column(Float, nullable=False)
    warning_threshold_value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ConcentrationSnapshot(Base):
    __tablename__ = 'concentration_snapshots'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    dimension = Column(String, nullable=False)
    bucket_name = Column(String, nullable=False)
    market_value = Column(Numeric(18, 6), nullable=False)
    portfolio_weight = Column(Float, nullable=False)
    position_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskLimit(Base):
    __tablename__ = 'risk_limits'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    metric_type = Column(String, nullable=False)
    scope_type = Column(String, nullable=False)  # GLOBAL, PORTFOLIO, SECTOR, ISSUER, RATING, COUNTRY
    scope_value = Column(String, nullable=True)  # e.g., '1' for portfolio_id, 'Technology' for sector
    direction = Column(String, nullable=False)   # MAXIMUM, MINIMUM
    warning_threshold = Column(Numeric(18, 6), nullable=True)
    limit_threshold = Column(Numeric(18, 6), nullable=False)
    severity = Column(String, nullable=False)    # WARNING, SOFT_LIMIT, HARD_LIMIT
    currency = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RiskEvaluationRun(Base):
    __tablename__ = 'risk_evaluation_runs'
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    model_status = Column(String, nullable=False) # e.g. FULL_FACTOR_MODEL, RATE_ONLY_MODEL
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    overall_status = Column(String, nullable=False) # PASS, WARNING, BREACH, FAILED
    evaluated_limit_count = Column(Integer, nullable=False)
    breach_count = Column(Integer, nullable=False)
    warning_count = Column(Integer, nullable=False)
    error_message = Column(String, nullable=True)

class RiskLimitResult(Base):
    __tablename__ = 'risk_limit_results'
    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(Integer, ForeignKey('risk_evaluation_runs.id'), nullable=False)
    risk_limit_id = Column(Integer, ForeignKey('risk_limits.id'), nullable=False)
    observed_value = Column(Numeric(18, 6), nullable=True)
    threshold_value = Column(Numeric(18, 6), nullable=False)
    utilization_percent = Column(Float, nullable=True)
    result_status = Column(String, nullable=False) # PASS, WARNING, BREACH, NOT_EVALUATED
    breach_amount = Column(Numeric(18, 6), nullable=True)
    metric_unit = Column(String, nullable=False)
    calculation_source = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Breach(Base):
    __tablename__ = 'breaches'
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    risk_limit_id = Column(Integer, ForeignKey('risk_limits.id'), nullable=False)
    first_evaluation_run_id = Column(Integer, ForeignKey('risk_evaluation_runs.id'), nullable=False)
    latest_evaluation_run_id = Column(Integer, ForeignKey('risk_evaluation_runs.id'), nullable=False)
    status = Column(String, nullable=False) # OPEN, ACKNOWLEDGED, RESOLVED
    severity = Column(String, nullable=False)
    observed_value = Column(Numeric(18, 6), nullable=False)
    threshold_value = Column(Numeric(18, 6), nullable=False)
    breach_amount = Column(Numeric(18, 6), nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String, nullable=True)
    assigned_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledgement_note = Column(String, nullable=True)
    resolution_note = Column(String, nullable=True)
    escalation_level = Column(Integer, default=0, nullable=False)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assigned_user = relationship("User", foreign_keys=[assigned_user_id])

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False) # LIMIT_CREATED, BREACH_OPENED, BREACH_ACKNOWLEDGED, etc
    entity_type = Column(String, nullable=False) # RISK_LIMIT, BREACH
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    request_id = Column(String, nullable=True)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actor_user = relationship("User")

class PortfolioRiskSnapshot(Base):
    __tablename__ = 'portfolio_risk_snapshots'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    snapshot_date = Column(Date, nullable=False, index=True)
    valuation_timestamp = Column(DateTime(timezone=True), nullable=False)

    total_market_value = Column(Numeric(18, 6), nullable=False)
    total_unrealized_pnl = Column(Numeric(18, 6), nullable=False)

    weighted_ytm = Column(Float, nullable=False)
    weighted_modified_duration = Column(Float, nullable=False)
    weighted_convexity = Column(Float, nullable=False)
    total_dv01 = Column(Numeric(18, 6), nullable=False)

    historical_var_95_1d = Column(Numeric(18, 6), nullable=True)
    expected_shortfall_95_1d = Column(Numeric(18, 6), nullable=True)
    parametric_var_95_1d = Column(Numeric(18, 6), nullable=True)

    worst_stress_scenario = Column(String(100), nullable=True)
    worst_stress_loss = Column(Numeric(18, 6), nullable=True)

    weighted_liquidity_score = Column(Float, nullable=True)
    liquidation_cost = Column(Numeric(18, 6), nullable=True)
    liquidation_cost_bps = Column(Float, nullable=True)
    weighted_days_to_liquidate = Column(Float, nullable=True)
    max_days_to_liquidate = Column(Integer, nullable=True)

    largest_issuer_concentration = Column(Float, nullable=True)
    largest_sector_concentration = Column(Float, nullable=True)

    overall_limit_status = Column(String(50), nullable=False)
    open_breach_count = Column(Integer, nullable=False)
    acknowledged_breach_count = Column(Integer, nullable=False)

    market_risk_model_status = Column(String(50), nullable=False)
    liquidity_model_type = Column(String(50), nullable=False)

    limitations = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'snapshot_date', name='uq_portfolio_snapshot_date'),
    )

class PipelineRun(Base):
    __tablename__ = 'pipeline_runs'

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String, nullable=False) # ALL, CATEGORY, DATASET, INCREMENTAL, BACKFILL
    status = Column(String, nullable=False) # PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED
    requested_start_date = Column(Date, nullable=True)
    requested_end_date = Column(Date, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    triggered_by = Column(String, nullable=False, default="SYSTEM")
    total_jobs = Column(Integer, nullable=False, default=0)
    successful_jobs = Column(Integer, nullable=False, default=0)
    failed_jobs = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSON, nullable=True)
    error_summary = Column(String, nullable=True)

    job_runs = relationship("PipelineJobRun", back_populates="pipeline_run", cascade="all, delete-orphan")

class PipelineJobRun(Base):
    __tablename__ = 'pipeline_job_runs'

    id = Column(Integer, primary_key=True, index=True)
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id', ondelete='CASCADE'), nullable=False)
    dataset_key = Column(String, nullable=False)
    status = Column(String, nullable=False) # PENDING, RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    rows_fetched = Column(Integer, nullable=False, default=0)
    rows_inserted = Column(Integer, nullable=False, default=0)
    rows_updated = Column(Integer, nullable=False, default=0)
    rows_rejected = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    pipeline_run = relationship("PipelineRun", back_populates="job_runs")

class DataQualityRun(Base):
    __tablename__ = 'data_quality_runs'

    id = Column(Integer, primary_key=True, index=True)
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id', ondelete='SET NULL'), nullable=True)
    status = Column(String, nullable=False) # PASS, WARNING, FAIL
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    datasets_checked = Column(Integer, nullable=False, default=0)
    checks_passed = Column(Integer, nullable=False, default=0)
    checks_warned = Column(Integer, nullable=False, default=0)
    checks_failed = Column(Integer, nullable=False, default=0)

    results = relationship("DataQualityResult", back_populates="data_quality_run", cascade="all, delete-orphan")

class DataQualityResult(Base):
    __tablename__ = 'data_quality_results'

    id = Column(Integer, primary_key=True, index=True)
    data_quality_run_id = Column(Integer, ForeignKey('data_quality_runs.id', ondelete='CASCADE'), nullable=False)
    dataset_key = Column(String, nullable=False)
    check_name = Column(String, nullable=False) # freshness, duplicates, nulls, continuity, min_history
    status = Column(String, nullable=False) # PASS, WARNING, FAIL
    observed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    message = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    data_quality_run = relationship("DataQualityRun", back_populates="results")

class AnalyticsRun(Base):
    __tablename__ = 'analytics_runs'

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    status = Column(String, nullable=False) # SUCCESS, PARTIAL_SUCCESS, FAILED
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    calculation_version = Column(String, nullable=True)
    model_status = Column(String, nullable=True) # AVAILABLE, DEGRADED, NO_DATA
    data_quality_status = Column(String, nullable=True) # PASS, WARNING, FAIL
    error_summary = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class InAppNotification(Base):
    __tablename__ = 'in_app_notifications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String, nullable=False) # e.g. breach, pipeline, data-quality
    severity = Column(String, nullable=False) # e.g. INFO, WARNING, SEVERE
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    entity_type = Column(String, nullable=True) # e.g. BREACH, PIPELINE_RUN
    entity_id = Column(Integer, nullable=True)

    user = relationship("User")


class SavedScenario(Base):
    __tablename__ = 'saved_scenarios'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    creator_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rate_2y_shock_bps = Column(Integer, default=0, nullable=False)
    rate_5y_shock_bps = Column(Integer, default=0, nullable=False)
    rate_10y_shock_bps = Column(Integer, default=0, nullable=False)
    rate_30y_shock_bps = Column(Integer, default=0, nullable=False)
    ig_spread_shock_bps = Column(Integer, default=0, nullable=False)
    hy_spread_shock_bps = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship("User")


class SavedScenarioRun(Base):
    __tablename__ = 'saved_scenario_runs'
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey('saved_scenarios.id', ondelete='CASCADE'), nullable=False)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False)
    valuation_date = Column(Date, nullable=False)
    executed_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    base_market_value = Column(Numeric(18, 6), nullable=False)
    stressed_market_value = Column(Numeric(18, 6), nullable=False)
    pnl_impact = Column(Numeric(18, 6), nullable=False)

    scenario = relationship("SavedScenario")
    portfolio = relationship("Portfolio")
    executor = relationship("User")
