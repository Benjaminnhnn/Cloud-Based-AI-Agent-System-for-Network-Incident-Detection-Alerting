from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        payload: dict | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            payload=payload,
            is_read=False,
        )
        db.add(notification)
        db.flush()
        return notification

    @staticmethod
    def list_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 30,
    ) -> list[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def unread_count(db: Session, user_id: int) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

    @staticmethod
    def mark_read(db: Session, user_id: int, notification_id: int) -> Notification:
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_read(db: Session, user_id: int) -> int:
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({Notification.is_read: True}, synchronize_session=False)
        )
        db.commit()
        return updated
