from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.notification import Notification, NotificationCount
from app.services.notification_service import NotificationService
from app.services.realtime_service import realtime_manager

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[Notification])
async def list_notifications(
    user_id: int,
    unread_only: bool = False,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    return NotificationService.list_notifications(db, user_id, unread_only=unread_only, limit=limit)


@router.get("/notifications/unread-count", response_model=NotificationCount)
async def unread_count(user_id: int, db: Session = Depends(get_db)):
    return {"unread_count": NotificationService.unread_count(db, user_id)}


@router.patch("/notifications/read-all", response_model=NotificationCount)
async def mark_all_read(user_id: int, db: Session = Depends(get_db)):
    NotificationService.mark_all_read(db, user_id)
    return {"unread_count": 0}


@router.patch("/notifications/{notification_id}/read", response_model=Notification)
async def mark_read(notification_id: int, user_id: int, db: Session = Depends(get_db)):
    return NotificationService.mark_read(db, user_id, notification_id)


@router.websocket("/ws/{user_id}")
async def realtime_websocket(websocket: WebSocket, user_id: int):
    await realtime_manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "realtime.connected", "user_id": user_id})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_manager.disconnect(user_id, websocket)
    except Exception:
        realtime_manager.disconnect(user_id, websocket)
