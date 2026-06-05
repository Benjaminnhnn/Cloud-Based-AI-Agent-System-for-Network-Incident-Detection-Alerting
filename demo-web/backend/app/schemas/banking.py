from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    id: int
    user_id: int
    account_number: str
    account_type: str
    balance: Decimal
    currency: str
    status: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Transaction(BaseModel):
    id: int
    reference_code: str
    transaction_type: str
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    amount: Decimal
    currency: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransferCreate(BaseModel):
    sender_user_id: int
    recipient_account_number: str = Field(min_length=10, max_length=32)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=255)


class AccountLookup(BaseModel):
    account_number: str
    account_name: str
    bank_name: str = "VietTien"


class TransferResult(BaseModel):
    reference_code: str
    from_account: Account
    to_account: Account
    debit_transaction: Transaction
    credit_transaction: Transaction
