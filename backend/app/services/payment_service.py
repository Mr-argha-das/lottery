import hashlib, hmac
from datetime import datetime
from urllib.parse import urlencode
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import Lottery, Payment, Ticket, Notification, AppSetting

def create(db:Session,user_id:str,lottery_id:str,key:str):
    existing=db.scalar(select(Payment).where(Payment.idempotency_key==key))
    if existing:
        if existing.user_id!=user_id: raise ValueError("Idempotency key conflict")
        return existing
    lottery=db.get(Lottery,lottery_id); now=datetime.now().astimezone()
    if not lottery or lottery.status!="ACTIVE" or lottery.join_deadline.replace(tzinfo=lottery.join_deadline.tzinfo or now.tzinfo)<=now: raise ValueError("Lottery is not open")
    count=db.scalar(select(func.count()).select_from(Ticket).where(Ticket.lottery_id==lottery_id)) or 0
    if count>=lottery.max_tickets: raise ValueError("Lottery sold out")
    p=Payment(user_id=user_id,lottery_id=lottery_id,amount=lottery.entry_price,status="PENDING",idempotency_key=key); db.add(p); db.commit(); db.refresh(p); return p
def deep_link(db:Session,p:Payment):
    s=get_settings(); upi=db.get(AppSetting,"upi_payee_id"); name=db.get(AppSetting,"upi_payee_name")
    q=urlencode({"pa":upi.value if upi else s.upi_payee_id,"pn":name.value if name else s.upi_payee_name,"am":str(p.amount),"cu":"INR","tr":p.id,"tn":"Lottery entry"}); return f"upi://pay?{q}"
def wallet_topup_link(db:Session):
    s=get_settings(); upi=db.get(AppSetting,"upi_payee_id"); name=db.get(AppSetting,"upi_payee_name")
    q=urlencode({"pa":upi.value if upi else s.upi_payee_id,"pn":name.value if name else s.upi_payee_name,"cu":"INR","tn":"Wallet top-up"})
    return f"upi://pay?{q}"
def verify_webhook(db:Session,payment_id:str,reference:str,status:str,signature:str):
    s=get_settings(); raw=f"{payment_id}|{reference}|{status}"; expected=hmac.new(s.webhook_secret.encode(),raw.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,expected): raise PermissionError("Invalid signature")
    p=db.get(Payment,payment_id)
    if not p: raise ValueError("Payment not found")
    if p.status=="SUCCESS": return p,db.scalar(select(Ticket).where(Ticket.payment_id==p.id))
    if status!="SUCCESS": p.status=status; p.provider_reference=reference; db.commit(); return p,None
    p.status="SUCCESS"; p.provider_reference=reference
    seq=(db.scalar(select(func.count()).select_from(Ticket).where(Ticket.lottery_id==p.lottery_id)) or 0)+1
    lottery=db.get(Lottery,p.lottery_id); ticket=Ticket(ticket_number=f"LOT-{lottery.result_at:%Y%m%d}-{seq:06d}",user_id=p.user_id,lottery_id=p.lottery_id,payment_id=p.id,entry_amount=p.amount)
    db.add_all([ticket,Notification(user_id=p.user_id,title="Ticket generated",body=f"Your ticket for {lottery.name} is confirmed.")]); db.commit(); db.refresh(ticket); return p,ticket
