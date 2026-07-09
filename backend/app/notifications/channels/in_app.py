from sqlalchemy.orm import Session
from app.notifications.types import NotificationCreate
from app.notifications.service import NotificationService
from app.notifications.templates import NotificationTemplateRenderer
import logging

logger = logging.getLogger(__name__)

class InAppChannel:
    @staticmethod
    def send(db: Session, user_id: int, event_type: str, severity: str, context: dict, entity_type: str = None, entity_id: int = None):
        """
        Sends an in-app notification by persisting it via NotificationService.
        """
        try:
            # Render template
            title, message = NotificationTemplateRenderer.render(event_type, context)
            
            obj_in = NotificationCreate(
                user_id=user_id,
                event_type=event_type,
                severity=severity,
                title=title,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id
            )
            return NotificationService.create_notification(db, obj_in)
        except Exception as e:
            logger.error(f"Failed to send in_app notification to user {user_id}: {e}")
            raise
