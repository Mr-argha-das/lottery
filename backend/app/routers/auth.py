import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Wallet, Referral, Session
from ..schemas import Register, Login, Refresh
from ..security import hash_password, verify_password, token, decode, token_hash
from ..config import get_settings

router=APIRouter(prefix="/api/auth",tags=["Authentication"])
def referral_code(): return secrets.token_hex(4).upper()
def pair(db,user):
    access=token(user.id,"access"); refresh=token(user.id,"refresh",minutes=get_settings().refresh_days*1440)
    db.add(Session(user_id=user.id,token_hash=token_hash(refresh),expires_at=datetime.now(timezone.utc)+timedelta(days=get_settings().refresh_days))); db.commit()
    return {"access_token":access,"refresh_token":refresh,"token_type":"bearer"}
@router.post("/register",status_code=201)
def register(body:Register,db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.mobile==body.mobile)): raise HTTPException(409,"Mobile already registered")
    referred=None
    if body.referral_code:
        referred=db.scalar(select(User).where(User.referral_code==body.referral_code.upper()))
        if not referred: raise HTTPException(400,"Invalid referral code")
    code=referral_code()
    while db.scalar(select(User).where(User.referral_code==code)): code=referral_code()
    u=User(full_name=body.full_name,mobile=body.mobile,password_hash=hash_password(body.password),referral_code=code); db.add(u); db.flush(); db.add(Wallet(user_id=u.id))
    if referred: db.add(Referral(referrer_id=referred.id,referred_id=u.id))
    db.commit(); return {"success":True,"data":pair(db,u)}
@router.post("/login")
def login(body:Login,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.mobile==body.mobile))
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
    if not u.is_active: raise HTTPException(403,"Account suspended")
    return {"success":True,"data":pair(db,u)}
@router.post("/refresh")
def refresh(body:Refresh,db:Session=Depends(get_db)):
    p=decode(body.refresh_token,"refresh"); sess=db.scalar(select(Session).where(Session.token_hash==token_hash(body.refresh_token),Session.revoked_at.is_(None)))
    if not sess: raise HTTPException(401,"Refresh token revoked")
    sess.revoked_at=datetime.now(timezone.utc); user=db.get(User,p["sub"]); db.commit(); return {"success":True,"data":pair(db,user)}
@router.post("/logout")
def logout(body:Refresh,db:Session=Depends(get_db)):
    sess=db.scalar(select(Session).where(Session.token_hash==token_hash(body.refresh_token)))
    if sess: sess.revoked_at=datetime.now(timezone.utc); db.commit()
    return {"success":True,"message":"Logged out"}

