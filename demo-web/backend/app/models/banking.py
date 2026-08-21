from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.user import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_number = Column(String(32), unique=True, index=True, nullable=False)
    account_type = Column(String(50), nullable=False, default="checking")
    balance = Column(Numeric(18, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="VND")
    status = Column(String(20), nullable=False, default="active")
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="accounts")


class LedgerTransaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    reference_code = Column(String(40), unique=True, index=True, nullable=False)
    transaction_type = Column(String(40), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="VND")
    description = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
