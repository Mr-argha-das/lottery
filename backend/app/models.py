import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def now(): return datetime.now(timezone.utc)
def uid(): return str(uuid.uuid4())

class LotteryStatus(str, enum.Enum):
    DRAFT="DRAFT"; SCHEDULED="SCHEDULED"; ACTIVE="ACTIVE"; JOINING_CLOSED="JOINING_CLOSED"; DRAW_PENDING="DRAW_PENDING"; COMPLETED="COMPLETED"; CANCELLED="CANCELLED"
class PaymentStatus(str, enum.Enum):
    CREATED="CREATED"; PENDING="PENDING"; SUCCESS="SUCCESS"; FAILED="FAILED"; EXPIRED="EXPIRED"; REFUNDED="REFUNDED"

class User(Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    full_name: Mapped[str]=mapped_column(String(100)); mobile: Mapped[str]=mapped_column(String(15), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255)); email: Mapped[str|None]=mapped_column(String(255), nullable=True)
    upi_id: Mapped[str|None]=mapped_column(String(100), nullable=True); address: Mapped[str|None]=mapped_column(Text, nullable=True)
    city: Mapped[str|None]=mapped_column(String(80), nullable=True); state: Mapped[str|None]=mapped_column(String(80), nullable=True); pincode: Mapped[str|None]=mapped_column(String(10), nullable=True)
    referral_code: Mapped[str]=mapped_column(String(12), unique=True, index=True); is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Session(Base):
    __tablename__="user_sessions"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True); token_hash: Mapped[str]=mapped_column(String, unique=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); revoked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class AdminUser(Base):
    __tablename__="admin_users"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    email: Mapped[str]=mapped_column(String, unique=True); password_hash: Mapped[str]=mapped_column(String); role: Mapped[str]=mapped_column(String, default="ADMIN"); is_active: Mapped[bool]=mapped_column(Boolean, default=True)

class Prize(Base):
    __tablename__="prizes"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str]=mapped_column(String); description: Mapped[str]=mapped_column(Text, default=""); prize_type: Mapped[str]=mapped_column(String, default="CASH")
    amount: Mapped[float|None]=mapped_column(Numeric(12,2), nullable=True); image_url: Mapped[str|None]=mapped_column(String, nullable=True); quantity: Mapped[int]=mapped_column(Integer, default=1); terms: Mapped[str]=mapped_column(Text, default="")

class Lottery(Base):
    __tablename__="lotteries"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str]=mapped_column(String); slug: Mapped[str]=mapped_column(String, unique=True); description: Mapped[str]=mapped_column(Text)
    banner_url: Mapped[str|None]=mapped_column(String, nullable=True); entry_price: Mapped[float]=mapped_column(Numeric(12,2)); start_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); join_deadline: Mapped[datetime]=mapped_column(DateTime(timezone=True)); result_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); max_tickets: Mapped[int]=mapped_column(Integer); min_tickets: Mapped[int]=mapped_column(Integer, default=1); status: Mapped[str]=mapped_column(String, default=LotteryStatus.DRAFT.value, index=True); terms: Mapped[str]=mapped_column(Text, default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class LotteryPrize(Base):
    __tablename__="lottery_prizes"; __table_args__=(UniqueConstraint("lottery_id","position"),)
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); lottery_id: Mapped[str]=mapped_column(ForeignKey("lotteries.id")); prize_id: Mapped[str]=mapped_column(ForeignKey("prizes.id")); position: Mapped[int]=mapped_column(Integer)

class Payment(Base):
    __tablename__="payments"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True); lottery_id: Mapped[str]=mapped_column(ForeignKey("lotteries.id"), index=True); amount: Mapped[float]=mapped_column(Numeric(12,2)); status: Mapped[str]=mapped_column(String, default="CREATED", index=True); provider: Mapped[str]=mapped_column(String, default="UPI"); provider_reference: Mapped[str|None]=mapped_column(String, unique=True, nullable=True); idempotency_key: Mapped[str]=mapped_column(String, unique=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Ticket(Base):
    __tablename__="tickets"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); ticket_number: Mapped[str]=mapped_column(String, unique=True, index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True); lottery_id: Mapped[str]=mapped_column(ForeignKey("lotteries.id"), index=True); payment_id: Mapped[str]=mapped_column(ForeignKey("payments.id"), unique=True); entry_amount: Mapped[float]=mapped_column(Numeric(12,2)); status: Mapped[str]=mapped_column(String, default="ELIGIBLE"); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Wallet(Base):
    __tablename__="wallets"; user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), primary_key=True); available_balance: Mapped[float]=mapped_column(Numeric(12,2), default=0); locked_balance: Mapped[float]=mapped_column(Numeric(12,2), default=0); lifetime_referral: Mapped[float]=mapped_column(Numeric(12,2), default=0); lifetime_winnings: Mapped[float]=mapped_column(Numeric(12,2), default=0); lifetime_spending: Mapped[float]=mapped_column(Numeric(12,2), default=0)
class WalletTransaction(Base):
    __tablename__="wallet_transactions"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True); amount: Mapped[float]=mapped_column(Numeric(12,2)); type: Mapped[str]=mapped_column(String); description: Mapped[str]=mapped_column(String); reference_id: Mapped[str]=mapped_column(String); balance_before: Mapped[float]=mapped_column(Numeric(12,2)); balance_after: Mapped[float]=mapped_column(Numeric(12,2)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class WithdrawalRequest(Base):
    __tablename__="withdrawal_requests"
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float]=mapped_column(Numeric(12,2))
    upi_id: Mapped[str]=mapped_column(String(100))
    status: Mapped[str]=mapped_column(String, default="PENDING", index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    processed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class Referral(Base):
    __tablename__="referrals"; __table_args__=(UniqueConstraint("referred_id"),)
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); referrer_id: Mapped[str]=mapped_column(ForeignKey("users.id")); referred_id: Mapped[str]=mapped_column(ForeignKey("users.id")); rewarded: Mapped[bool]=mapped_column(Boolean, default=False); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Draw(Base):
    __tablename__="draws"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); lottery_id: Mapped[str]=mapped_column(ForeignKey("lotteries.id"), unique=True); eligible_ticket_ids: Mapped[str]=mapped_column(Text); eligible_count: Mapped[int]=mapped_column(Integer); commitment_hash: Mapped[str]=mapped_column(String); seed_hex: Mapped[str]=mapped_column(String); algorithm: Mapped[str]=mapped_column(String, default="SHA256-RANK-v1"); verification_hash: Mapped[str]=mapped_column(String); executed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class DrawWinner(Base):
    __tablename__="draw_winners"; __table_args__=(UniqueConstraint("draw_id","position"), UniqueConstraint("draw_id","ticket_id"))
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); draw_id: Mapped[str]=mapped_column(ForeignKey("draws.id")); ticket_id: Mapped[str]=mapped_column(ForeignKey("tickets.id")); position: Mapped[int]=mapped_column(Integer)

class Notification(Base):
    __tablename__="notifications"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True); title: Mapped[str]=mapped_column(String); body: Mapped[str]=mapped_column(Text); is_read: Mapped[bool]=mapped_column(Boolean, default=False); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class AuditLog(Base):
    __tablename__="audit_logs"; id: Mapped[str]=mapped_column(String, primary_key=True, default=uid); admin_id: Mapped[str|None]=mapped_column(String, nullable=True); action: Mapped[str]=mapped_column(String, index=True); entity: Mapped[str]=mapped_column(String); entity_id: Mapped[str]=mapped_column(String); old_value: Mapped[str|None]=mapped_column(Text, nullable=True); new_value: Mapped[str|None]=mapped_column(Text, nullable=True); ip: Mapped[str|None]=mapped_column(String, nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class AppSetting(Base):
    __tablename__="app_settings"; key: Mapped[str]=mapped_column(String, primary_key=True); value: Mapped[str]=mapped_column(Text)
