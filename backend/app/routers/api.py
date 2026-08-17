import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import *
from ..schemas import ProfileUpdate, PaymentCreate, Webhook
from ..security import current_user
from ..services import payment_service

router=APIRouter(prefix="/api")
def obj(x): return {c.name:getattr(x,c.name) for c in x.__table__.columns}
@router.get("/users/me")
def me(user=Depends(current_user),db:Session=Depends(get_db)):
    data=obj(user); data.pop("password_hash"); data["wallet"]=obj(db.get(Wallet,user.id)); return {"success":True,"data":data}
@router.put("/users/me")
def update(body:ProfileUpdate,user=Depends(current_user),db:Session=Depends(get_db)):
    for k,v in body.model_dump(exclude_unset=True).items(): setattr(user,k,v)
    db.commit(); return {"success":True,"data":obj(user)}
@router.get("/lotteries")
def lotteries(db:Session=Depends(get_db)):
    rows=db.scalars(select(Lottery).where(Lottery.status.in_(["ACTIVE","SCHEDULED"])).order_by(Lottery.result_at)).all(); return {"success":True,"data":[obj(x) for x in rows]}
@router.get("/lotteries/{lottery_id}")
def lottery(lottery_id:str,db:Session=Depends(get_db)):
    x=db.get(Lottery,lottery_id)
    if not x: raise HTTPException(404,"Lottery not found")
    d=obj(x); d["ticket_count"]=db.scalar(select(func.count()).select_from(Ticket).where(Ticket.lottery_id==x.id)); d["prizes"]=[obj(p) for p in db.scalars(select(Prize).join(LotteryPrize,Prize.id==LotteryPrize.prize_id).where(LotteryPrize.lottery_id==x.id).order_by(LotteryPrize.position))]; return {"success":True,"data":d}
@router.post("/payments/create",status_code=201)
def payment_create(body:PaymentCreate,user=Depends(current_user),db:Session=Depends(get_db)):
    try: p=payment_service.create(db,user.id,body.lottery_id,body.idempotency_key)
    except ValueError as e: raise HTTPException(409,str(e))
    return {"success":True,"message":"Awaiting provider verification","data":{**obj(p),"upi_deep_link":payment_service.deep_link(db,p)}}
@router.get("/payments/{payment_id}")
def payment(payment_id:str,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.get(Payment,payment_id)
    if not p or p.user_id!=user.id: raise HTTPException(404,"Payment not found")
    return {"success":True,"data":obj(p)}
@router.post("/payments/webhook",include_in_schema=False)
def webhook(body:Webhook,db:Session=Depends(get_db)):
    try: p,t=payment_service.verify_webhook(db,body.payment_id,body.provider_reference,body.status,body.signature)
    except PermissionError as e: raise HTTPException(401,str(e))
    except ValueError as e: raise HTTPException(404,str(e))
    return {"success":True,"data":{"payment":obj(p),"ticket":obj(t) if t else None}}
@router.get("/tickets")
def tickets(user=Depends(current_user),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Ticket).where(Ticket.user_id==user.id).order_by(Ticket.created_at.desc()))]}
@router.get("/wallet")
def wallet(user=Depends(current_user),db:Session=Depends(get_db)): return {"success":True,"data":obj(db.get(Wallet,user.id))}
@router.get("/wallet/transactions")
def wallet_tx(user=Depends(current_user),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(WalletTransaction).where(WalletTransaction.user_id==user.id).order_by(WalletTransaction.created_at.desc()))]}
@router.get("/referrals")
def referrals(user=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Referral).where(Referral.referrer_id==user.id)).all(); return {"success":True,"data":{"code":user.referral_code,"total":len(rows),"successful":sum(r.rewarded for r in rows)}}
@router.get("/notifications")
def notifications(user=Depends(current_user),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()))]}
@router.put("/notifications/{notification_id}/read")
def read_notification(notification_id:str,user=Depends(current_user),db:Session=Depends(get_db)):
    n=db.get(Notification,notification_id)
    if not n or n.user_id!=user.id: raise HTTPException(404,"Notification not found")
    n.is_read=True; db.commit(); return {"success":True}
@router.get("/winners")
def winners(db:Session=Depends(get_db)):
    rows=db.execute(select(DrawWinner,Ticket,Lottery,User).join(Ticket,DrawWinner.ticket_id==Ticket.id).join(Draw,DrawWinner.draw_id==Draw.id).join(Lottery,Draw.lottery_id==Lottery.id).join(User,Ticket.user_id==User.id).order_by(Draw.executed_at.desc(),DrawWinner.position)).all()
    def masked(name):
        return " ".join((part[0]+"*"*max(3,len(part)-1)) for part in name.split())
    data=[]
    for w,t,l,u in rows:
        prize=db.scalar(select(Prize).join(LotteryPrize,Prize.id==LotteryPrize.prize_id).where(LotteryPrize.lottery_id==l.id,LotteryPrize.position==w.position))
        data.append({"position":w.position,"ticket_number":t.ticket_number,"lottery":l.name,"winner":masked(u.full_name),"prize":prize.title if prize else f"Position {w.position} prize","draw_id":w.draw_id})
    return {"success":True,"data":data}
@router.get("/draws/{draw_id}/verify")
def verify_draw(draw_id:str,db:Session=Depends(get_db)):
    d=db.get(Draw,draw_id)
    if not d: raise HTTPException(404,"Draw not found")
    wins=db.execute(select(DrawWinner,Ticket).join(Ticket).where(DrawWinner.draw_id==d.id).order_by(DrawWinner.position)).all()
    return {"success":True,"data":{**obj(d),"eligible_ticket_ids":json.loads(d.eligible_ticket_ids),"winners":[{"position":w.position,"ticket_number":t.ticket_number} for w,t in wins]}}
