from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class Notification(BaseModel):
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    payload: Optional[dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCount(BaseModel):
    unread_count: int
