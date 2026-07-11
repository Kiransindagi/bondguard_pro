from sqlalchemy.orm import Session
import logging

from app.db.models import User, Role
from app.notifications.types import NotificationEventType, NotificationSeverity
from app.notifications.service import NotificationService
from app.notifications.channels import ChannelRegistry
from app.notifications.preferences import NotificationPreferences

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    @staticmethod
    def dispatch_event(
        db: Session,
        event_type: NotificationEventType,
        severity: NotificationSeverity,
        title: str,
        message: str,
        entity_type: str = None,
        entity_id: int = None,
        context: dict = None
    ):
        if context is None:
            context = {"title": title, "message": message}
            
        # Map event types to roles that should receive them
        target_roles = ["ADMIN"]
        
        if event_type in [
            NotificationEventType.LIMIT_BREACH,
            NotificationEventType.SEVERE_BREACH,
            NotificationEventType.BREACH_ACKNOWLEDGED,
            NotificationEventType.BREACH_RESOLVED,
            NotificationEventType.SEVERE_STRESS_LOSS,
            NotificationEventType.LIQUIDITY_DETERIORATION,
            NotificationEventType.RATE_MODEL_UNAVAILABLE,
            NotificationEventType.MODEL_DEGRADATION
        ]:
            target_roles.extend(["RISK_MANAGER", "PORTFOLIO_MANAGER", "ANALYST"])

        # Fetch active users in target roles
        users = db.query(User).join(User.roles).filter(
            Role.name.in_(target_roles),
        User.is_active.is_(True)
        ).all()

        for user in users:
            try:
                channels = NotificationPreferences.get_user_channels(
                    user_id=user.id,
                    event_type=event_type.value if hasattr(event_type, 'value') else event_type,
                    severity=severity.value if hasattr(severity, 'value') else severity
                )
                
                for channel_name in channels:
                    channel_class = ChannelRegistry.get_channel(channel_name)
                    if channel_class:
                        channel_class.send(
                            db=db,
                            user_id=user.id,
                            event_type=event_type.value if hasattr(event_type, 'value') else event_type,
                            severity=severity.value if hasattr(severity, 'value') else severity,
                            context=context,
                            entity_type=entity_type,
                            entity_id=entity_id
                        )
            except Exception as e:
                logger.error(f"Failed to dispatch notification to user {user.id}: {e}")

    @staticmethod
    def dispatch_breach_event(
        db: Session,
        breach,
        event_type: NotificationEventType,
        severity: NotificationSeverity,
        title: str,
        message: str
    ):
        # Enforce deduplication rules
        if not NotificationService.should_notify_breach(db, breach, event_type, severity):
            logger.info(f"Deduplicated breach notification for breach ID {breach.id}")
            return

        context = {
            "title": title,
            "message": message,
            "limit_id": breach.risk_limit_id,
            "portfolio_id": breach.portfolio_id,
            "severity": severity.value if hasattr(severity, 'value') else severity
        }

        NotificationDispatcher.dispatch_event(
            db=db,
            event_type=event_type,
            severity=severity,
            title=title,
            message=message,
            entity_type="BREACH",
            entity_id=breach.id,
            context=context
        )
