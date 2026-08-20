import hashlib, json, re, secrets
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import (AuditLog, Draw, DrawWinner, Lottery, LotteryPrize,
                      Notification, Prize, Ticket, Wallet, WalletTransaction)

ALGORITHM="SHA256-RANK-v1"
def cash_amount(db:Session, lottery_id:str, position:int)->Decimal:
    prize=db.scalar(select(Prize).join(LotteryPrize,Prize.id==LotteryPrize.prize_id).where(LotteryPrize.lottery_id==lottery_id,LotteryPrize.position==position))
    if not prize or prize.prize_type!="CASH": return Decimal("0")
    if prize.amount is not None: return Decimal(str(prize.amount))
    match=re.search(r"(?:₹|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)",prize.title,re.IGNORECASE)
    return Decimal(match.group(1).replace(",","")) if match else Decimal("0")

def execute(db:Session, lottery:Lottery, admin_id:str, ip:str|None=None)->Draw:
    if db.scalar(select(Draw).where(Draw.lottery_id==lottery.id)): raise ValueError("Draw already executed")
    tickets=list(db.scalars(select(Ticket).where(Ticket.lottery_id==lottery.id,Ticket.status=="ELIGIBLE").order_by(Ticket.id)).all())
    if len(tickets)<max(3,lottery.min_tickets): raise ValueError("Not enough eligible tickets")
    ids=[t.id for t in tickets]; frozen=json.dumps(ids,separators=(",",":")); seed=secrets.token_bytes(32)
    commitment=hashlib.sha256(seed).hexdigest()
    ranked=sorted(tickets,key=lambda t: hashlib.sha256(seed+t.id.encode()).digest())[:3]
    verification=hashlib.sha256((lottery.id+frozen+seed.hex()+ALGORITHM+"".join(t.id for t in ranked)).encode()).hexdigest()
    draw=Draw(lottery_id=lottery.id,eligible_ticket_ids=frozen,eligible_count=len(ids),commitment_hash=commitment,seed_hex=seed.hex(),algorithm=ALGORITHM,verification_hash=verification)
    db.add(draw); db.flush()
    for pos,t in enumerate(ranked,1):
        db.add(DrawWinner(draw_id=draw.id,ticket_id=t.id,position=pos))
        amount=cash_amount(db,lottery.id,pos)
        if amount>0:
            wallet=db.get(Wallet,t.user_id) or Wallet(user_id=t.user_id)
            before=Decimal(str(wallet.available_balance or 0)); after=before+amount
            wallet.available_balance=after; wallet.lifetime_winnings=Decimal(str(wallet.lifetime_winnings or 0))+amount
            db.add(wallet); db.add(WalletTransaction(user_id=t.user_id,amount=amount,type="PRIZE_CREDIT",description=f"Position {pos} prize • {lottery.name}",reference_id=f"{draw.id}:{pos}",balance_before=before,balance_after=after))
            db.add(Notification(user_id=t.user_id,title="Prize credited",body=f"₹{amount:,.0f} has been added to your wallet for winning position {pos} in {lottery.name}."))
    lottery.status="COMPLETED"; db.add(AuditLog(admin_id=admin_id,action="EXECUTE_DRAW",entity="lottery",entity_id=lottery.id,new_value=json.dumps({"draw_id":draw.id,"hash":verification}),ip=ip)); db.commit(); db.refresh(draw); return draw
