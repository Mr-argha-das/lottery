from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import AdminUser, Lottery, Prize, LotteryPrize, AppSetting
from app.security import hash_password
from app.config import get_settings

Base.metadata.create_all(engine); db=SessionLocal(); s=get_settings(); now=datetime.now(timezone.utc)
if not db.scalar(select(AdminUser).where(AdminUser.email=="admin@example.com")):
    db.add(AdminUser(email="admin@example.com",password_hash=hash_password("ChangeMe123!"),role="SUPER_ADMIN"))
for name,slug,price,first,second,third in [("Mega Bike Lottery","mega-bike",100,"Royal Enfield Bike","₹25,000","₹10,000"),("Mega Car Lottery","mega-car",500,"Premium Car","₹50,000","₹20,000")]:
    if db.scalar(select(Lottery).where(Lottery.slug==slug)): continue
    lot=Lottery(name=name,slug=slug,description=f"Win big in the transparent {name} draw.",entry_price=price,start_at=now-timedelta(days=1),join_deadline=now+timedelta(days=7),result_at=now+timedelta(days=8),max_tickets=20000,status="ACTIVE",terms="18+ only. Subject to applicable laws.",banner_url=f"https://picsum.photos/seed/{slug}/1200/700"); db.add(lot); db.flush()
    for pos,title in enumerate((first,second,third),1):
        p=Prize(title=title,description=f"Position {pos} prize",prize_type="PHYSICAL" if pos==1 else "CASH"); db.add(p); db.flush(); db.add(LotteryPrize(lottery_id=lot.id,prize_id=p.id,position=pos))
db.merge(AppSetting(key="referral_reward",value="20")); db.merge(AppSetting(key="referral_enabled",value="true")); db.merge(AppSetting(key="wallet_topup_deep_link",value="")); db.merge(AppSetting(key="terms_text",value="DhanLaxmi is available only to eligible adults. Lottery participation and wallet credits are subject to applicable laws and verified payment confirmation.")); db.merge(AppSetting(key="privacy_text",value="We use your account, payment reference and delivery information only to operate draws, issue prizes and meet legal obligations.")); db.merge(AppSetting(key="support_contact",value="support@dhanlaxmi.app")); db.commit(); db.close()
print("Seeded. Admin: admin@example.com / ChangeMe123! (change immediately)")
