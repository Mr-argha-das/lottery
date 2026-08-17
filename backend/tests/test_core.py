import hashlib, hmac
from datetime import datetime,timedelta,timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Lottery,Ticket,Payment,AdminUser,Draw,DrawWinner
from app.security import hash_password

def auth(client,mobile="9999999999",ref=None):
    body={"full_name":"Test User","mobile":mobile,"password":"Secure123!"}
    if ref: body["referral_code"]=ref
    r=client.post("/api/auth/register",json=body); assert r.status_code==201
    return r.json()["data"]["access_token"]
def lottery(db,status="ACTIVE"):
    now=datetime.now(timezone.utc); x=Lottery(name="Fair Draw",slug="fair-"+status.lower(),description="test",entry_price=100,start_at=now-timedelta(days=1),join_deadline=now+timedelta(days=1),result_at=now+timedelta(days=2),max_tickets=100,status=status);db.add(x);db.commit();return x
def test_registration_login_and_self_referral_guard(client):
    t=auth(client); me=client.get("/api/users/me",headers={"Authorization":f"Bearer {t}"}); assert me.status_code==200; code=me.json()["data"]["referral_code"]
    r=client.post("/api/auth/register",json={"full_name":"Same","mobile":"9999999999","password":"Secure123!","referral_code":code}); assert r.status_code==409
def test_closed_lottery_rejected(client):
    t=auth(client);db=SessionLocal();x=lottery(db,"JOINING_CLOSED");db.close()
    r=client.post("/api/payments/create",headers={"Authorization":f"Bearer {t}"},json={"lottery_id":x.id,"idempotency_key":"unique-key-1"});assert r.status_code==409
def test_signed_payment_is_idempotent(client):
    t=auth(client);db=SessionLocal();x=lottery(db);db.close(); headers={"Authorization":f"Bearer {t}"}
    p=client.post("/api/payments/create",headers=headers,json={"lottery_id":x.id,"idempotency_key":"unique-key-2"}).json()["data"]
    raw=f"{p['id']}|provider-1|SUCCESS";sig=hmac.new(b"development-webhook-secret",raw.encode(),hashlib.sha256).hexdigest();body={"payment_id":p["id"],"provider_reference":"provider-1","status":"SUCCESS","signature":sig}
    assert client.post("/api/payments/webhook",json=body).status_code==200;assert client.post("/api/payments/webhook",json=body).status_code==200
    db=SessionLocal();assert len(db.scalars(select(Ticket)).all())==1;db.close()
def test_draw_unique_and_irreversible(client):
    db=SessionLocal();x=lottery(db,"DRAW_PENDING");a=AdminUser(email="a@b.com",password_hash=hash_password("Secure123!"),role="SUPER_ADMIN");db.add(a);db.flush()
    for i in range(5):
        from app.models import User
        u=User(full_name=f"User {i}",mobile=f"900000000{i}",password_hash="x",referral_code=f"REF{i}");db.add(u);db.flush();p=Payment(user_id=u.id,lottery_id=x.id,amount=100,status="SUCCESS",idempotency_key=f"k{i}");db.add(p);db.flush();db.add(Ticket(ticket_number=f"LOT-X-{i}",user_id=u.id,lottery_id=x.id,payment_id=p.id,entry_amount=100))
    db.commit();db.close();r=client.post("/api/admin/login",json={"email":"a@b.com","password":"Secure123!"});h={"Authorization":f"Bearer {r.json()['data']['access_token']}"}
    assert client.post(f"/api/admin/draws/{x.id}/execute",headers=h).status_code==200;assert client.post(f"/api/admin/draws/{x.id}/execute",headers=h).status_code==409
    db=SessionLocal();wins=db.scalars(select(DrawWinner)).all();assert len(wins)==3 and len({w.ticket_id for w in wins})==3;db.close()

