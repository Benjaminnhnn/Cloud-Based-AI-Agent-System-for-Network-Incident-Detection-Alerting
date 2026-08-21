from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.banking import Account, AccountLookup, Transaction, TransferCreate, TransferResult
from app.schemas.notification import Notification
from app.services.banking_service import BankingService
from app.services.realtime_service import realtime_manager

router = APIRouter(prefix="/api", tags=["banking"])


@router.get("/accounts", response_model=list[Account])
async def list_accounts(user_id: int | None = None, db: Session = Depends(get_db)):
    return BankingService.list_accounts(db, user_id=user_id)


@router.get("/accounts/lookup/{account_number}", response_model=AccountLookup)
async def lookup_account(account_number: str, db: Session = Depends(get_db)):
    return BankingService.lookup_account(db, account_number)


@router.get("/transactions", response_model=list[Transaction])
async def list_transactions(
    user_id: int | None = None,
    account_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return BankingService.list_transactions(db, user_id=user_id, account_id=account_id, limit=limit)


@router.post("/transfers", response_model=TransferResult, status_code=201)
async def create_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    from_account, to_account, debit, credit, sender_notification, receiver_notification = BankingService.transfer(db, payload)

    sender_event = {
        "type": "banking.updated",
        "reason": "transfer_out",
        "notification": Notification.model_validate(sender_notification).model_dump(mode="json"),
        "account": Account.model_validate(from_account).model_dump(mode="json"),
        "transaction": Transaction.model_validate(debit).model_dump(mode="json"),
    }
    receiver_event = {
        "type": "banking.updated",
        "reason": "transfer_in",
        "notification": Notification.model_validate(receiver_notification).model_dump(mode="json"),
        "account": Account.model_validate(to_account).model_dump(mode="json"),
        "transaction": Transaction.model_validate(credit).model_dump(mode="json"),
    }
    await realtime_manager.send_to_user(from_account.user_id, sender_event)
    await realtime_manager.send_to_user(to_account.user_id, receiver_event)

    return {
        "reference_code": debit.reference_code.removesuffix("-D"),
        "from_account": from_account,
        "to_account": to_account,
        "debit_transaction": debit,
        "credit_transaction": credit,
    }
