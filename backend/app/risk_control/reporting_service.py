import logging
from datetime import datetime
from decimal import Decimal

from app.db.models import (
    Breach,
    Portfolio,
    RiskEvaluationRun,
    RiskLimit,
    RiskLimitResult,
)
from app.risk_control.enums import MetricType
from app.risk_control.metric_registry import registry
from app.schemas.risk_control import (
    ActiveBreachItem,
    BreachSummary,
    ConcentrationSection,
    LimitResultItem,
    LimitSummary,
    LiquidityRiskSection,
    MarketRiskSection,
    ModelGovernance,
    PortfolioRiskSection,
    ReportMetadata,
    RiskReportResponse,
    StressRiskSection,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ReportingService:
    @staticmethod
    def generate_report(db: Session, portfolio_id: int) -> RiskReportResponse:
        # Get portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError("Portfolio not found")
            
        # Get latest evaluation run
        run = db.query(RiskEvaluationRun).filter(
            RiskEvaluationRun.portfolio_id == portfolio_id
        ).order_by(RiskEvaluationRun.id.desc()).first()
        
        if not run:
            raise ValueError("No risk evaluation found for this portfolio. Run an evaluation first.")

        # Get limit results for this run
        limit_results = db.query(RiskLimitResult).filter(
            RiskLimitResult.evaluation_run_id == run.id
        ).all()
        
        limit_ids = [r.risk_limit_id for r in limit_results]
        limits = db.query(RiskLimit).filter(RiskLimit.id.in_(limit_ids)).all()
        limits_map = {limit_obj.id: limit_obj for limit_obj in limits}
        
        # To get the limitations and model statuses properly, we need to ask the adapters again
        # or we could have stored them in RiskLimitResult. Since we didn't store all of them,
        # we can recalculate them quickly from adapters to populate the report, OR 
        # we can fetch the underlying service data. The prompt says:
        # "The report service must compose existing persisted evaluation results and authoritative service outputs."
        # So we fetch from the authoritative services.
        
        # Portfolio Risk Section
        from app.api.v1.risk import get_portfolio_risk_summary
        port_metrics = get_portfolio_risk_summary(portfolio_id, run.valuation_date, db)
        portfolio_risk = PortfolioRiskSection(
            total_market_value=port_metrics.total_market_value if port_metrics else None,
            weighted_modified_duration=port_metrics.weighted_modified_duration if port_metrics else None,
            total_dv01=port_metrics.total_dv01 if port_metrics else None
        )
        
        # Market Risk Section
        from app.api.v1.market_risk import (
            get_expected_shortfall,
            get_historical_var,
            get_parametric_var,
        )
        hist_var, param_var, es = None, None, None
        mr_model_status = "AVAILABLE"
        mr_limitations = None
        try:
            h_res = get_historical_var(portfolio_id, confidence_level=0.95, horizon_days=1, db=db)
            hist_var = Decimal(h_res.get("var_currency", 0))
            mr_model_status = h_res.get("model_type", "AVAILABLE")
            if mr_model_status != "FULL_FACTOR_MODEL":
                mr_limitations = "Missing credit spread risk"
                
            p_res = get_parametric_var(portfolio_id, confidence_level=0.95, horizon_days=1, db=db)
            param_var = Decimal(p_res.get("var_currency", 0))
            
            es_res = get_expected_shortfall(portfolio_id, confidence_level=0.95, db=db)
            es = Decimal(es_res.get("expected_shortfall_currency", 0))
        except Exception as e:
            logger.error(f"Failed to generate market risk section: {e}", exc_info=True)
            try:
                from app.risk_engine.market_risk.availability import (
                    check_model_availability,
                )
                avail = check_model_availability(db)
                mr_model_status = avail.model_status.value
                mr_limitations = avail.limitations
            except Exception:
                mr_model_status = "ERROR"
                mr_limitations = str(e)
            
        market_risk = MarketRiskSection(
            historical_var=hist_var,
            parametric_var=param_var,
            expected_shortfall=es,
            model_status=mr_model_status,
            limitations=mr_limitations
        )
        
        from app.db.models import StressScenario
        from app.risk_engine.stress_testing.portfolio_stress import compare_scenarios
        worst_name, worst_code, worst_pnl, worst_pct = None, None, None, None
        try:
            predefined = db.query(StressScenario).filter(StressScenario.is_predefined.is_(True)).all()
            if predefined:
                scenario_ids = [s.id for s in predefined]
                comp = compare_scenarios(db, portfolio_id, scenario_ids, run.valuation_date)
                if comp and comp.scenarios:
                    w = comp.scenarios[0]
                    worst_name = w.scenario_name
                    worst_code = w.scenario_name
                    worst_pnl = Decimal(str(w.total_pnl))
                    mv = portfolio_risk.total_market_value
                    worst_pct = (worst_pnl / mv * 100) if mv and mv > 0 else Decimal(0)
        except Exception:
            pass
            
        stress_risk = StressRiskSection(
            worst_scenario_name=worst_name,
            worst_scenario_code=worst_code,
            pnl=worst_pnl,
            loss_percent=worst_pct
        )
        
        # Liquidity Risk Section
        from app.services.liquidity_snapshot import generate_liquidity_snapshot
        liq_score, liq_cost, liq_cost_bps, w_days, m_days = None, None, None, None, None
        liq_model_label = "CHARACTERISTIC_BASED_PROXY_V1"
        liq_limitations = "Synthetic capacity proxy"
        try:
            snap = generate_liquidity_snapshot(db, portfolio_id, run.valuation_date)
            if snap:
                liq_score = Decimal(snap.weighted_liquidity_score)
                liq_cost = Decimal(snap.estimated_total_liquidation_cost)
                liq_cost_bps = Decimal(snap.estimated_total_liquidation_cost_bps)
                w_days = Decimal(snap.weighted_days_to_liquidate)
                m_days = Decimal(snap.maximum_days_to_liquidate)
        except Exception as e:
            liq_model_label = "ERROR"
            liq_limitations = str(e)
            
        liquidity_risk = LiquidityRiskSection(
            liquidity_score=liq_score,
            liquidation_cost=liq_cost,
            liquidation_cost_bps=liq_cost_bps,
            weighted_days_to_liquidate=w_days,
            max_days_to_liquidate=m_days,
            model_label=liq_model_label,
            limitations=liq_limitations
        )
        
        # Concentration Section
        from app.api.v1.liquidity_risk import get_portfolio_concentration
        c_issuer, c_issuer_w, c_sector, c_sector_w, c_single = None, None, None, None, None
        try:
            iss_c = get_portfolio_concentration(portfolio_id, "issuer", db)
            if iss_c and iss_c.breakdown:
                c_issuer = iss_c.breakdown[0].name
                c_issuer_w = Decimal(iss_c.breakdown[0].portfolio_weight)
                
            sec_c = get_portfolio_concentration(portfolio_id, "sector", db)
            if sec_c and sec_c.breakdown:
                c_sector = sec_c.breakdown[0].name
                c_sector_w = Decimal(sec_c.breakdown[0].portfolio_weight)
                
            bond_c = get_portfolio_concentration(portfolio_id, "bond_id", db)
            if bond_c and bond_c.breakdown:
                c_single = Decimal(bond_c.breakdown[0].portfolio_weight)
        except Exception:
            pass
            
        concentration = ConcentrationSection(
            largest_issuer=c_issuer,
            largest_issuer_weight=c_issuer_w,
            largest_sector=c_sector,
            largest_sector_weight=c_sector_w,
            max_single_position_weight=c_single
        )
        
        # Limits and Breaches
        eval_count = len(limit_results)
        pass_c = sum(1 for r in limit_results if r.result_status == "PASS")
        warn_c = sum(1 for r in limit_results if r.result_status == "WARNING")
        breach_c = sum(1 for r in limit_results if r.result_status == "BREACH")
        not_eval_c = sum(1 for r in limit_results if r.result_status == "NOT_EVALUATED")
        
        limit_summary = LimitSummary(
            evaluated_limit_count=eval_count,
            pass_count=pass_c,
            warning_count=warn_c,
            breach_count=breach_c,
            not_evaluated_count=not_eval_c
        )
        
        limit_items = []
        for r in limit_results:
            r_limit = limits_map.get(r.risk_limit_id)
            if not r_limit:
                continue
            # try to re-evaluate model status limitations
            metric = MetricType(r_limit.metric_type)
            adapter = registry.get_adapter(metric)
            m_status = r.calculation_source
            m_lim = None
            if adapter:
                try:
                    norm = adapter.get_value(metric, portfolio_id, run.valuation_date, db)
                    m_status = norm.model_status
                    m_lim = norm.limitations
                except Exception:
                    pass
                    
            limit_items.append(LimitResultItem(
                metric_type=r_limit.metric_type,
                observed_value=Decimal(r.observed_value) if r.observed_value is not None else None,
                threshold_value=Decimal(r.threshold_value),
                utilization_percent=float(r.utilization_percent) if r.utilization_percent is not None else None,
                status=r.result_status,
                unit=r.metric_unit,
                calculation_source=r.calculation_source,
                model_status=m_status,
                limitations=m_lim
            ))
            
        all_breaches = db.query(Breach).filter(Breach.portfolio_id == portfolio_id).all()
        open_b = sum(1 for b in all_breaches if b.status == "OPEN")
        ack_b = sum(1 for b in all_breaches if b.status == "ACKNOWLEDGED")
        res_b = sum(1 for b in all_breaches if b.status == "RESOLVED")
        
        breach_summary = BreachSummary(open_count=open_b, acknowledged_count=ack_b, resolved_count=res_b)
        
        active_breach_items = []
        for b in all_breaches:
            if b.status in ("OPEN", "ACKNOWLEDGED"):
                b_limit = db.query(RiskLimit).filter(RiskLimit.id == b.risk_limit_id).first()
                if not b_limit:
                    continue
                active_breach_items.append(ActiveBreachItem(
                    breach_id=b.id,
                    limit_code=b_limit.code,
                    metric_type=b_limit.metric_type,
                    severity=b.severity,
                    status=b.status,
                    observed_value=Decimal(b.observed_value),
                    threshold_value=Decimal(b.threshold_value),
                    breach_amount=Decimal(b.breach_amount),
                    opened_at=b.opened_at,
                    acknowledged_at=b.acknowledged_at,
                    assigned_to=b.assigned_to
                ))
                
        # Model Governance
        active_models = ["DETERMINISTIC_PRICING", "STRESS_TESTING", "CONCENTRATION_ANALYTICS"]
        degraded = []
        proxy = ["CHARACTERISTIC_BASED_PROXY_V1"]
        lims = []
        
        if mr_model_status == "RATE_ONLY_MODEL":
            degraded.append("MARKET_RISK_RATE_ONLY")
            lims.append("Credit spread risk excluded because aligned spread history is insufficient.")
        else:
            active_models.append("MARKET_RISK_FULL_FACTOR")
            
        lims.append("Liquidity capacity is model-estimated using characteristic-based proxy assumptions and is not observed market ADV.")
        
        model_gov = ModelGovernance(
            active_models=active_models,
            degraded_models=degraded,
            proxy_models=proxy,
            limitations=lims
        )
        
        return RiskReportResponse(
            portfolio={"id": portfolio.id, "name": portfolio.name, "base_currency": portfolio.base_currency, "benchmark": getattr(portfolio, "benchmark", None)},
            report_metadata=ReportMetadata(
                valuation_date=run.valuation_date,
                generated_at=datetime.utcnow(),
                evaluation_run_id=run.id,
                overall_status=run.overall_status
            ),
            portfolio_risk=portfolio_risk,
            market_risk=market_risk,
            stress_risk=stress_risk,
            liquidity_risk=liquidity_risk,
            concentration=concentration,
            limit_summary=limit_summary,
            limit_results=limit_items,
            breach_summary=breach_summary,
            active_breaches=active_breach_items,
            model_governance=model_gov
        )
