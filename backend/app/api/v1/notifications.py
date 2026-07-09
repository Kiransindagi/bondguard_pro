from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.auth.dependencies import get_current_user, PermissionChecker
from app.auth.permissions import NOTIFICATION_READ, NOTIFICATION_MANAGE
from app.db.models import User
from app.notifications import NotificationService

router = APIRouter()

@router.get("")
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for the current authenticated user.
    """
    return NotificationService.get_user_notifications(db, current_user.id)

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the unread notification count.
    """
    return {"unread_count": NotificationService.get_unread_count(db, current_user.id)}

@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read.
    """
    notif = NotificationService.mark_as_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found or not owned by user")
    return notif

@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all unread notifications as read.
    """
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {"marked_read_count": count}
