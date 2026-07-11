from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.models import InAppNotification
from app.notifications.types import NotificationCreate, NotificationEventType, NotificationSeverity

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def create_notification(db: Session, obj_in: NotificationCreate) -> InAppNotification:
        db_notif = InAppNotification(
            user_id=obj_in.user_id,
            event_type=obj_in.event_type.value if hasattr(obj_in.event_type, 'value') else obj_in.event_type,
            severity=obj_in.severity.value if hasattr(obj_in.severity, 'value') else obj_in.severity,
            title=obj_in.title,
            message=obj_in.message,
            entity_type=obj_in.entity_type,
            entity_id=obj_in.entity_id,
            is_read=False
        )
        db.add(db_notif)
        db.commit()
        db.refresh(db_notif)
        return db_notif

    @staticmethod
    def get_user_notifications(db: Session, user_id: int, limit: int = 50) -> List[InAppNotification]:
        return db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id
        ).order_by(InAppNotification.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        return db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.is_read.is_(False)
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[InAppNotification]:
        notif = db.query(InAppNotification).filter(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        unread = db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.is_read.is_(False)
        ).all()
        for notif in unread:
            notif.is_read = True
        db.commit()
        return len(unread)

    @staticmethod
    def should_notify_breach(db: Session, breach, event_type: NotificationEventType, severity: NotificationSeverity) -> bool:
        # Deduplication check
        last_notif = db.query(InAppNotification).filter(
            InAppNotification.entity_type == "BREACH",
            InAppNotification.entity_id == breach.id
        ).order_by(InAppNotification.created_at.desc()).first()

        if not last_notif:
            return True # First time

        # If previous notification was resolved, but we are sending a new alert
        if last_notif.event_type == NotificationEventType.BREACH_RESOLVED.value and event_type != NotificationEventType.BREACH_RESOLVED:
            return True

        # If the state/event_type has changed
        if last_notif.event_type != event_type.value:
            return True

        # If severity has increased
        if severity == NotificationSeverity.SEVERE and last_notif.severity != NotificationSeverity.SEVERE.value:
            return True

        # If breach amount has increased by more than 10% (crosses escalation threshold)
        # Parse last breach amount or compare from current breach object
        # We can also check if breach.observed_value changed significantly
        if last_notif.message:
            try:
                # Store value in metadata or estimate from observed vs previous
                # For robust check, if breach amount changed by more than 10%
                # we can fetch previous AuditEvents if needed, or simply compare observed values
                pass
            except Exception:
                pass

        return False
