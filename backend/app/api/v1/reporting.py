from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import io
import csv

from app.db.database import get_db
from app.db.models import PortfolioRiskSnapshot
from app.reporting.snapshot_service import SnapshotService
from app.reporting.executive_report import ExecutiveReportService

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import PORTFOLIO_READ, REPORT_GENERATE

router = APIRouter()

@router.post("/portfolios/{portfolio_id}/snapshots", dependencies=[Depends(PermissionChecker(REPORT_GENERATE))])
def generate_snapshot(portfolio_id: int, valuation_date: date = None, db: Session = Depends(get_db)):
    if not valuation_date:
        valuation_date = date.today()
    try:
        snapshot = SnapshotService.generate_snapshot(db, portfolio_id, valuation_date)
        return {"status": "success", "snapshot_id": snapshot.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios/{portfolio_id}/snapshots", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_snapshots(
    portfolio_id: int, 
    date_from: Optional[date] = None, 
    date_to: Optional[date] = None, 
    limit: int = 30, 
    db: Session = Depends(get_db)
):
    query = db.query(PortfolioRiskSnapshot).filter(PortfolioRiskSnapshot.portfolio_id == portfolio_id)
    if date_from:
        query = query.filter(PortfolioRiskSnapshot.snapshot_date >= date_from)
    if date_to:
        query = query.filter(PortfolioRiskSnapshot.snapshot_date <= date_to)
        
    return query.order_by(PortfolioRiskSnapshot.snapshot_date.asc()).limit(limit).all()

@router.get("/portfolios/{portfolio_id}/snapshots/latest", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_latest_snapshot(portfolio_id: int, db: Session = Depends(get_db)):
    snapshot = db.query(PortfolioRiskSnapshot).filter(
        PortfolioRiskSnapshot.portfolio_id == portfolio_id
    ).order_by(PortfolioRiskSnapshot.snapshot_date.desc()).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshots found for portfolio")
        
    return snapshot

@router.get("/portfolios/{portfolio_id}/executive-report", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_executive_report(portfolio_id: int, snapshot_date: Optional[date] = None, db: Session = Depends(get_db)):
    if not snapshot_date:
        latest = db.query(PortfolioRiskSnapshot).filter(
            PortfolioRiskSnapshot.portfolio_id == portfolio_id
        ).order_by(PortfolioRiskSnapshot.snapshot_date.desc()).first()
        if not latest:
            raise HTTPException(status_code=404, detail="No snapshots found for portfolio")
        snapshot_date = latest.snapshot_date
        
    try:
        return ExecutiveReportService.generate_report(db, portfolio_id, snapshot_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios/{portfolio_id}/executive-report.csv", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def export_snapshots_csv(portfolio_id: int, db: Session = Depends(get_db)):
    snapshots = db.query(PortfolioRiskSnapshot).filter(
        PortfolioRiskSnapshot.portfolio_id == portfolio_id
    ).order_by(PortfolioRiskSnapshot.snapshot_date.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Snapshot Date", "Market Value (USD)", "Modified Duration", "Total DV01", 
        "Historical VaR 95%", "Worst Stress Loss", "Liquidity Score", 
        "Open Breaches", "Market Risk Model Status"
    ]
    writer.writerow(headers)
    
    for s in snapshots:
        writer.writerow([
            s.snapshot_date.isoformat(),
            float(s.total_market_value),
            s.weighted_modified_duration,
            float(s.total_dv01),
            float(s.historical_var_95_1d) if s.historical_var_95_1d else "N/A",
            float(s.worst_stress_loss) if s.worst_stress_loss else "N/A",
            s.weighted_liquidity_score if s.weighted_liquidity_score else "N/A",
            s.open_breach_count,
            s.market_risk_model_status
        ])
        
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=snapshots.csv"})

@router.get("/portfolios/{portfolio_id}/executive-report.pdf", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def export_executive_report_pdf(portfolio_id: int, snapshot_date: Optional[date] = None, db: Session = Depends(get_db)):
    if not snapshot_date:
        latest = db.query(PortfolioRiskSnapshot).filter(
            PortfolioRiskSnapshot.portfolio_id == portfolio_id
        ).order_by(PortfolioRiskSnapshot.snapshot_date.desc()).first()
        if not latest:
            raise HTTPException(status_code=404, detail="No snapshots found for portfolio")
        snapshot_date = latest.snapshot_date
        
    try:
        report = ExecutiveReportService.generate_report(db, portfolio_id, snapshot_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []
    
    # Title
    flowables.append(Paragraph("BondGuard Pro Executive Risk Report", styles['Title']))
    flowables.append(Spacer(1, 12))
    
    # Disclaimer
    flowables.append(Paragraph("FOR DEMONSTRATION AND EDUCATIONAL PURPOSES. NOT INVESTMENT ADVICE. DEMONSTRATION POLICY LIMITS ARE NOT REGULATORY REQUIREMENTS.", styles['Italic']))
    flowables.append(Spacer(1, 12))
    
    # Metadata
    flowables.append(Paragraph(f"Portfolio: {report['portfolio']['name']}", styles['Normal']))
    flowables.append(Paragraph(f"Snapshot Date: {report['report_metadata']['snapshot_date']}", styles['Normal']))
    flowables.append(Paragraph(f"Overall Risk Status: {report['executive_summary']['overall_risk_status']}", styles['Normal']))
    flowables.append(Spacer(1, 12))
    
    # Portfolio Risk
    flowables.append(Paragraph("Portfolio Risk Summary", styles['Heading2']))
    data = [
        ["Metric", "Value"],
        ["Market Value", f"{report['portfolio_risk']['total_market_value']:,.2f}"],
        ["Modified Duration", f"{report['portfolio_risk']['weighted_modified_duration']:.2f}"],
        ["Total DV01", f"{report['portfolio_risk']['total_dv01']:,.2f}"]
    ]
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    flowables.append(t)
    flowables.append(Spacer(1, 12))
    
    # Market Risk
    flowables.append(Paragraph("Market Risk", styles['Heading2']))
    flowables.append(Paragraph(f"Model Status: {report['executive_summary']['market_risk_model_status']}", styles['Normal']))
    if report['market_risk']['historical_var_95_1d']:
        flowables.append(Paragraph(f"Historical VaR (95%, 1D): {report['market_risk']['historical_var_95_1d']:,.2f}", styles['Normal']))
    else:
        flowables.append(Paragraph("Historical VaR: N/A", styles['Normal']))
    flowables.append(Spacer(1, 12))
    
    # Active Breaches
    flowables.append(Paragraph(f"Active Breaches ({len(report['active_breaches'])})", styles['Heading2']))
    if len(report['active_breaches']) > 0:
        b_data = [["Code", "Metric", "Status", "Amount"]]
        for b in report['active_breaches']:
            b_data.append([b['limit_code'], b['metric_type'], b['status'], f"{b['breach_amount']:,.2f}"])
        bt = Table(b_data)
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        flowables.append(bt)
        
    doc.build(flowables)
    
    return Response(
        content=output.getvalue(), 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=executive_report.pdf"}
    )
