from datetime import datetime
from decimal import Decimal
import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.banking import Account, LedgerTransaction
from app.models.user import User
from app.schemas.banking import TransferCreate
from app.services.notification_service import NotificationService


class BankingService:
    @staticmethod
    def generate_account_number() -> str:
        return f"970436{secrets.randbelow(10_000_000_000):010d}"

    @staticmethod
    def generate_unique_account_number(db: Session) -> str:
        for _ in range(20):
            account_number = BankingService.generate_account_number()
            if not db.query(Account.id).filter(Account.account_number == account_number).first():
                return account_number
        raise RuntimeError("Unable to generate a unique account number")

    @staticmethod
    def generate_reference_code() -> str:
        return f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def ensure_primary_account(db: Session, user: User, opening_balance: Decimal | None = None) -> Account:
        account = (
            db.query(Account)
            .filter(Account.user_id == user.id, Account.is_primary.is_(True))
            .first()
        )
        if account:
            return account

        balance = opening_balance if opening_balance is not None else Decimal("10000000.00")
        account = Account(
            user_id=user.id,
            account_number=BankingService.generate_unique_account_number(db),
            account_type="checking",
            balance=balance,
            currency="VND",
            status="active",
            is_primary=True,
        )
        db.add(account)
        db.flush()
        return account

    @staticmethod
    def seed_missing_accounts(db: Session) -> None:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        changed = False
        for user in users:
            existing = db.query(Account).filter(Account.user_id == user.id).first()
            if not existing:
                BankingService.ensure_primary_account(db, user)
                changed = True
        if changed:
            db.commit()

    @staticmethod
    def list_accounts(db: Session, user_id: int | None = None) -> list[Account]:
        query = db.query(Account).order_by(Account.id)
        if user_id is not None:
            query = query.filter(Account.user_id == user_id)
        return query.all()

    @staticmethod
    def lookup_account(db: Session, account_number: str) -> dict:
        account = (
            db.query(Account)
            .filter(Account.account_number == account_number.strip(), Account.status == "active")
            .first()
        )
        if not account or not account.user or not account.user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient account not found")
        return {
            "account_number": account.account_number,
            "account_name": account.user.full_name or account.user.username,
            "bank_name": "VietTien",
        }

    @staticmethod
    def list_transactions(
        db: Session,
        user_id: int | None = None,
        account_id: int | None = None,
        limit: int = 50,
    ) -> list[LedgerTransaction]:
        query = db.query(LedgerTransaction)

        if account_id is not None:
            query = query.filter(
                or_(
                    LedgerTransaction.from_account_id == account_id,
                    LedgerTransaction.to_account_id == account_id,
                )
            )
        elif user_id is not None:
            account_ids = [row.id for row in db.query(Account.id).filter(Account.user_id == user_id).all()]
            if not account_ids:
                return []
            query = query.filter(
                or_(
                    LedgerTransaction.from_account_id.in_(account_ids),
                    LedgerTransaction.to_account_id.in_(account_ids),
                )
            )

        return query.order_by(LedgerTransaction.created_at.desc()).limit(limit).all()

    @staticmethod
    def transfer(
        db: Session,
        payload: TransferCreate,
    ) -> tuple[Account, Account, LedgerTransaction, LedgerTransaction, object, object]:
        amount = payload.amount.quantize(Decimal("0.01"))

        from_account = (
            db.query(Account)
            .filter(
                Account.user_id == payload.sender_user_id,
                Account.is_primary.is_(True),
                Account.status == "active",
            )
            .with_for_update()
            .first()
        )
        if not from_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found")

        to_account = (
            db.query(Account)
            .filter(
                Account.account_number == payload.recipient_account_number.strip(),
                Account.status == "active",
            )
            .with_for_update()
            .first()
        )
        if not to_account or not to_account.user or not to_account.user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient account not found")

        if from_account.id == to_account.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account")

        if from_account.currency != to_account.currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Currency mismatch")

        if Decimal(from_account.balance) < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

        reference = BankingService.generate_reference_code()
        recipient_name = to_account.user.full_name or to_account.user.username
        description = payload.description or f"Transfer to {recipient_name}"

        from_account.balance = Decimal(from_account.balance) - amount
        to_account.balance = Decimal(to_account.balance) + amount

        debit = LedgerTransaction(
            reference_code=f"{reference}-D",
            transaction_type="transfer_out",
            from_account_id=from_account.id,
            to_account_id=None,
            amount=amount,
            currency=from_account.currency,
            description=description,
            status="completed",
        )
        credit = LedgerTransaction(
            reference_code=f"{reference}-C",
            transaction_type="transfer_in",
            from_account_id=None,
            to_account_id=to_account.id,
            amount=amount,
            currency=from_account.currency,
            description=description,
            status="completed",
        )

        db.add(debit)
        db.add(credit)
        sender_notification = NotificationService.create(
            db,
            user_id=from_account.user_id,
            notification_type="transfer_out",
            title="Chuyển tiền thành công",
            message=f"Bạn đã chuyển {amount:,.0f} {from_account.currency} đến {recipient_name}.",
            payload={
                "reference_code": reference,
                "amount": str(amount),
                "currency": from_account.currency,
                "account_number": to_account.account_number,
            },
        )
        receiver_notification = NotificationService.create(
            db,
            user_id=to_account.user_id,
            notification_type="transfer_in",
            title="Bạn vừa nhận được tiền",
            message=f"Tài khoản của bạn vừa nhận {amount:,.0f} {from_account.currency}.",
            payload={
                "reference_code": reference,
                "amount": str(amount),
                "currency": from_account.currency,
                "account_number": from_account.account_number,
            },
        )
        db.commit()
        db.refresh(from_account)
        db.refresh(to_account)
        db.refresh(debit)
        db.refresh(credit)
        db.refresh(sender_notification)
        db.refresh(receiver_notification)
        return from_account, to_account, debit, credit, sender_notification, receiver_notification
