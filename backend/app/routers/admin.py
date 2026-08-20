from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import *
from ..schemas import AdminLogin, LotteryCreate, LotteryUpdate, PrizeCreate, SettingUpdate
from ..security import verify_password, token, current_admin, elevated_admin
from ..services.draw_service import execute

router=APIRouter(prefix="/api/admin",tags=["Admin"])
def obj(x): return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def sync_prizes(db:Session,lottery:Lottery,prizes):
    if not prizes: return
    if {p.position for p in prizes}!={1,2,3}: raise HTTPException(422,"Configure exactly 1st, 2nd and 3rd prizes")
    for item in prizes:
        if item.prize_type not in {"CASH","PHYSICAL"}: raise HTTPException(422,"Prize type must be CASH or PHYSICAL")
        if item.prize_type=="CASH" and item.amount is None: raise HTTPException(422,f"Cash amount is required for position {item.position}")
        link=db.scalar(select(LotteryPrize).where(LotteryPrize.lottery_id==lottery.id,LotteryPrize.position==item.position))
        prize=db.get(Prize,link.prize_id) if link else None
        if not prize:
            prize=Prize(title=item.title); db.add(prize); db.flush(); db.add(LotteryPrize(lottery_id=lottery.id,prize_id=prize.id,position=item.position))
        prize.title=item.title; prize.description=f"Position {item.position} prize"; prize.prize_type=item.prize_type; prize.amount=item.amount if item.prize_type=="CASH" else None
def lottery_obj(db:Session,x:Lottery):
    data=obj(x); rows=db.execute(select(LotteryPrize,Prize).join(Prize,LotteryPrize.prize_id==Prize.id).where(LotteryPrize.lottery_id==x.id).order_by(LotteryPrize.position)).all(); data["prizes"]=[{**obj(p),"position":link.position} for link,p in rows]; return data
@router.post("/login")
def login(body:AdminLogin,db:Session=Depends(get_db)):
    a=db.scalar(select(AdminUser).where(AdminUser.email==body.email))
    if not a or not verify_password(body.password,a.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"success":True,"data":{"access_token":token(a.id,"admin",a.role),"role":a.role}}
@router.get("/overview")
def overview(admin=Depends(current_admin),db:Session=Depends(get_db)):
    count=lambda m: db.scalar(select(func.count()).select_from(m)) or 0
    return {"success":True,"data":{"users":count(User),"active_lotteries":db.scalar(select(func.count()).select_from(Lottery).where(Lottery.status=="ACTIVE")),"tickets":count(Ticket),"payments":count(Payment),"winners":count(DrawWinner)}}
@router.post("/lotteries",status_code=201)
def create_lottery(body:LotteryCreate,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    if not(body.start_at<body.join_deadline<body.result_at): raise HTTPException(422,"Dates must be chronological")
    x=Lottery(**body.model_dump(exclude={"prizes"})); db.add(x); db.flush(); sync_prizes(db,x,body.prizes); db.add(AuditLog(admin_id=admin.id,action="CREATE",entity="lottery",entity_id=x.id,new_value=x.name)); db.commit(); return {"success":True,"data":lottery_obj(db,x)}
@router.put("/lotteries/{lottery_id}")
def update_lottery(lottery_id:str,body:LotteryUpdate,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    x=db.get(Lottery,lottery_id)
    if not x: raise HTTPException(404,"Lottery not found")
    if x.status=="COMPLETED": raise HTTPException(409,"Completed lottery cannot be edited")
    old=obj(x)
    changes=body.model_dump(exclude_unset=True,exclude={"prizes"})
    for key,value in changes.items(): setattr(x,key,value)
    if body.prizes is not None: sync_prizes(db,x,body.prizes)
    if not(x.start_at<x.join_deadline<x.result_at): raise HTTPException(422,"Dates must be chronological")
    db.add(AuditLog(admin_id=admin.id,action="UPDATE",entity="lottery",entity_id=x.id,old_value=str(old),new_value=str(body.model_dump(exclude_unset=True)))); db.commit(); return {"success":True,"data":lottery_obj(db,x)}
@router.delete("/lotteries/{lottery_id}")
def delete_lottery(lottery_id:str,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    x=db.get(Lottery,lottery_id)
    if not x: raise HTTPException(404,"Lottery not found")
    ticket_count=db.scalar(select(func.count()).select_from(Ticket).where(Ticket.lottery_id==x.id)) or 0
    if ticket_count or x.status=="COMPLETED": raise HTTPException(409,"Lottery with tickets or completed draw cannot be deleted; cancel it instead")
    db.add(AuditLog(admin_id=admin.id,action="DELETE",entity="lottery",entity_id=x.id,old_value=x.name)); db.delete(x); db.commit(); return {"success":True,"message":"Lottery deleted"}
@router.post("/prizes",status_code=201)
def create_prize(body:PrizeCreate,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    x=Prize(**body.model_dump()); db.add(x); db.commit(); return {"success":True,"data":obj(x)}
@router.post("/draws/{lottery_id}/execute")
def draw(lottery_id:str,request:Request,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    lottery=db.get(Lottery,lottery_id)
    if not lottery or lottery.status not in {"DRAW_PENDING","JOINING_CLOSED"}: raise HTTPException(409,"Lottery is not draw-ready")
    try: d=execute(db,lottery,admin.id,request.client.host if request.client else None)
    except ValueError as e: raise HTTPException(409,str(e))
    return {"success":True,"message":"Draw completed permanently","data":obj(d)}
@router.get("/users")
def users(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[{k:v for k,v in obj(x).items() if k!="password_hash"} for x in db.scalars(select(User).order_by(User.created_at.desc()))]}
@router.get("/lotteries")
def lotteries(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[lottery_obj(db,x) for x in db.scalars(select(Lottery).order_by(Lottery.created_at.desc()))]}
@router.get("/tickets")
def tickets(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Ticket).order_by(Ticket.created_at.desc()))]}
@router.get("/payments")
def payments(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Payment).order_by(Payment.created_at.desc()))]}
@router.get("/wallet-transactions")
def wallet_transactions(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(WalletTransaction).order_by(WalletTransaction.created_at.desc()))]}
@router.get("/withdrawals")
def withdrawals(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(WithdrawalRequest).order_by(WithdrawalRequest.created_at.desc()))]}
@router.get("/referrals")
def referrals(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Referral).order_by(Referral.created_at.desc()))]}
@router.get("/winners")
def winners(admin=Depends(current_admin),db:Session=Depends(get_db)):
    rows=db.execute(select(DrawWinner,Ticket,User,Lottery).join(Ticket,DrawWinner.ticket_id==Ticket.id).join(User,Ticket.user_id==User.id).join(Draw,DrawWinner.draw_id==Draw.id).join(Lottery,Draw.lottery_id==Lottery.id).order_by(Draw.executed_at.desc(),DrawWinner.position)).all()
    return {"success":True,"data":[{"position":w.position,"lottery":l.name,"ticket_number":t.ticket_number,"winner":u.full_name,"mobile":u.mobile,"draw_id":w.draw_id} for w,t,u,l in rows]}
@router.get("/notifications")
def notifications(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(Notification).order_by(Notification.created_at.desc()))]}
@router.get("/settings")
def settings(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(AppSetting).order_by(AppSetting.key))]}
@router.get("/audit-logs")
def audits(admin=Depends(current_admin),db:Session=Depends(get_db)): return {"success":True,"data":[obj(x) for x in db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()))]}
@router.put("/settings/{key}")
def setting(key:str,body:SettingUpdate,admin=Depends(elevated_admin),db:Session=Depends(get_db)):
    x=db.get(AppSetting,key) or AppSetting(key=key,value=body.value); x.value=body.value; db.add(x); db.add(AuditLog(admin_id=admin.id,action="UPDATE_SETTING",entity="setting",entity_id=key,new_value=body.value)); db.commit(); return {"success":True}
