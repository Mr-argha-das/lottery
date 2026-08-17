import hashlib, json, secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Draw, DrawWinner, Lottery, Ticket, AuditLog

ALGORITHM="SHA256-RANK-v1"
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
    for pos,t in enumerate(ranked,1): db.add(DrawWinner(draw_id=draw.id,ticket_id=t.id,position=pos))
    lottery.status="COMPLETED"; db.add(AuditLog(admin_id=admin_id,action="EXECUTE_DRAW",entity="lottery",entity_id=lottery.id,new_value=json.dumps({"draw_id":draw.id,"hash":verification}),ip=ip)); db.commit(); db.refresh(draw); return draw

