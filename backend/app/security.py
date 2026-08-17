import hashlib, secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User, AdminUser

passwords=PasswordHash.recommended(); bearer=HTTPBearer(); settings=get_settings()
def hash_password(v:str)->str: return passwords.hash(v)
def verify_password(v:str,h:str)->bool: return passwords.verify(v,h)
def token(subject:str, kind:str, role:str|None=None, minutes:int|None=None)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=minutes or settings.access_minutes)
    data={"sub":subject,"type":kind,"exp":exp,"jti":secrets.token_hex(12)}
    if role: data["role"]=role
    return jwt.encode(data,settings.jwt_secret_key,algorithm="HS256")
def decode(v:str, kind:str):
    try:
        p=jwt.decode(v,settings.jwt_secret_key,algorithms=["HS256"])
        if p.get("type")!=kind: raise ValueError()
        return p
    except Exception: raise HTTPException(401,"Invalid or expired token")
def token_hash(v:str)->str: return hashlib.sha256(v.encode()).hexdigest()
def current_user(c:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    p=decode(c.credentials,"access"); user=db.get(User,p["sub"])
    if not user or not user.is_active: raise HTTPException(401,"Inactive account")
    return user
def current_admin(c:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    p=decode(c.credentials,"admin"); admin=db.get(AdminUser,p["sub"])
    if not admin or not admin.is_active: raise HTTPException(403,"Admin access required")
    return admin
def elevated_admin(admin=Depends(current_admin)):
    if admin.role not in {"SUPER_ADMIN","ADMIN"}: raise HTTPException(403,"Elevated permission required")
    return admin

