from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import User, Role, InAppNotification
from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
from app.notifications.service import NotificationService
from app.notifications.types import NotificationCreate
from app.db.models import Breach, Portfolio, RiskLimit


def test_notifications_dispatcher(db_session: Session):
    """Dispatcher must persist an in-app notification when a valid admin user exists."""
    admin_role = db_session.query(Role).filter_by(name="ADMIN").first()
    if not admin_role:
        admin_role = Role(name="ADMIN", description="Admin")
        db_session.add(admin_role)
        db_session.commit()

    user = User(username="admin_notif_test2", email="admin_test2@bg.com",
                hashed_password="pw", is_active=True)
    user.roles.append(admin_role)
    db_session.add(user)
    db_session.commit()

    NotificationDispatcher.dispatch_event(
        db=db_session,
        event_type=NotificationEventType.RATE_MODEL_UNAVAILABLE,
        severity=NotificationSeverity.INFO,
        title="Rate model unavailable",
        message="System alert",
        entity_type="SYSTEM",
        entity_id=99
    )

    notif = db_session.query(InAppNotification).filter_by(entity_id=99).first()
    assert notif is not None
    assert notif.title == "Rate Model Unavailable"
    assert notif.is_read is False


def test_workflow_deduplication(db_session: Session):
    """
    Breach deduplication: First call must allow notification.
    Second identical call must be suppressed by the service layer.
    """
    portfolio = Portfolio(name="Dedup Port")
    db_session.add(portfolio)
    db_session.commit()

    rl = RiskLimit(code="L1DUP", name="Limit Dup", metric_type="VAR",
                   scope_type="GLOBAL", direction="MAXIMUM",
                   limit_threshold=Decimal(100), severity="CRITICAL",
                   effective_from=date.today())
    db_session.add(rl)
    db_session.commit()

    breach = Breach(
        portfolio_id=portfolio.id, risk_limit_id=rl.id,
        first_evaluation_run_id=1, latest_evaluation_run_id=1,
        status="OPEN", severity="CRITICAL",
        observed_value=Decimal(150), threshold_value=Decimal(100),
        breach_amount=Decimal(50), opened_at=date.today()
    )
    db_session.add(breach)
    db_session.commit()

    # First evaluation: should notify
    should_notify1 = NotificationService.should_notify_breach(
        db_session, breach,
        NotificationEventType.LIMIT_BREACH, NotificationSeverity.SEVERE
    )
    assert should_notify1 is True

    # Create the notification to simulate dispatch
    notif_create = NotificationCreate(
        user_id=1,
        event_type=NotificationEventType.LIMIT_BREACH,
        severity=NotificationSeverity.SEVERE,
        title="Breach Alert",
        message="Breach detected",
        entity_type="BREACH",
        entity_id=breach.id
    )
    NotificationService.create_notification(db_session, notif_create)

    # Second evaluation: identical type+severity should be deduplicated
    should_notify2 = NotificationService.should_notify_breach(
        db_session, breach,
        NotificationEventType.LIMIT_BREACH, NotificationSeverity.SEVERE
    )
    assert should_notify2 is False


def test_notification_severity_escalation_always_fires(db_session: Session):
    """SEVERE notifications must bypass deduplication even after a previous INFO notification."""
    portfolio = Portfolio(name="Escalation Port")
    db_session.add(portfolio)
    db_session.commit()

    rl = RiskLimit(code="L2ESC", name="Limit Esc", metric_type="VAR",
                   scope_type="GLOBAL", direction="MAXIMUM",
                   limit_threshold=Decimal(100), severity="CRITICAL",
                   effective_from=date.today())
    db_session.add(rl)
    db_session.commit()

    breach = Breach(
        portfolio_id=portfolio.id, risk_limit_id=rl.id,
        first_evaluation_run_id=2, latest_evaluation_run_id=2,
        status="OPEN", severity="CRITICAL",
        observed_value=Decimal(120), threshold_value=Decimal(100),
        breach_amount=Decimal(20), opened_at=date.today()
    )
    db_session.add(breach)
    db_session.commit()

    # Simulate a prior INFO-level notification
    notif_create = NotificationCreate(
        user_id=1,
        event_type=NotificationEventType.LIMIT_BREACH,
        severity=NotificationSeverity.INFO,
        title="Breach Info",
        message="Mild breach",
        entity_type="BREACH",
        entity_id=breach.id
    )
    NotificationService.create_notification(db_session, notif_create)

    # Now a SEVERE notification should override deduplication
    should_escalate = NotificationService.should_notify_breach(
        db_session, breach,
        NotificationEventType.LIMIT_BREACH, NotificationSeverity.SEVERE
    )
    assert should_escalate is True
