from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import (
    AdminUser, AppSetting, Draw, DrawWinner, Lottery, LotteryPrize, Payment,
    Prize, Ticket, User,
)
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

# Historical demo draws keep the Winners screen populated without weakening the
# production draw service. These records are clearly seed data and are idempotent.
demo_draws = [
    ("Summer Bumper Draw", "summer-bumper-2026", 200,
     ("₹2,00,000 Cash", "₹75,000 Cash", "₹25,000 Cash"),
     (("Aarav Sharma", "9876504101", "Jaipur", "DL-SB-48291"),
      ("Priya Verma", "9876504102", "Lucknow", "DL-SB-73104"),
      ("Mohammed Arif", "9876504103", "Bhopal", "DL-SB-26587"))),
    ("Festive Gold Draw", "festive-gold-2026", 150,
     ("50g Gold Coin", "₹50,000 Cash", "₹20,000 Cash"),
     (("Neha Patel", "9876504104", "Ahmedabad", "DL-FG-90842"),
      ("Rohan Singh", "9876504105", "Chandigarh", "DL-FG-15476"),
      ("Kavita Joshi", "9876504106", "Pune", "DL-FG-62319"))),
]
for draw_index, (name, slug, price, prize_titles, winners) in enumerate(demo_draws):
    if db.scalar(select(Lottery).where(Lottery.slug == slug)):
        continue
    lot = Lottery(name=name, slug=slug,
        description=f"Completed and independently verifiable {name}.",
        entry_price=price, start_at=now-timedelta(days=45-draw_index*12),
        join_deadline=now-timedelta(days=32-draw_index*12),
        result_at=now-timedelta(days=31-draw_index*12), max_tickets=10000,
        min_tickets=3, status="COMPLETED", terms="18+ only. Demo seed draw.",
        banner_url=f"https://picsum.photos/seed/{slug}/1200/700")
    db.add(lot); db.flush()
    for position, title in enumerate(prize_titles, 1):
        prize = Prize(title=title, description=f"Position {position} prize",
            prize_type="PHYSICAL" if "Gold" in title else "CASH")
        db.add(prize); db.flush()
        db.add(LotteryPrize(lottery_id=lot.id, prize_id=prize.id,
                            position=position))
    tickets = []
    for position, (full_name, mobile, city, ticket_number) in enumerate(winners, 1):
        user = User(full_name=full_name, mobile=mobile,
            password_hash=hash_password("DemoWinner123!"), city=city,
            state="India", referral_code=f"WIN{draw_index}{position}26")
        db.add(user); db.flush()
        payment = Payment(user_id=user.id, lottery_id=lot.id, amount=price,
            status="SUCCESS", provider="SEED_DEMO",
            provider_reference=f"DEMO-{slug}-{position}",
            idempotency_key=f"demo-{slug}-{position}")
        db.add(payment); db.flush()
        ticket = Ticket(ticket_number=ticket_number, user_id=user.id,
            lottery_id=lot.id, payment_id=payment.id, entry_amount=price,
            status="ELIGIBLE")
        db.add(ticket); db.flush(); tickets.append(ticket)
    draw = Draw(lottery_id=lot.id,
        eligible_ticket_ids=str([ticket.id for ticket in tickets]).replace("'", '"'),
        eligible_count=len(tickets), commitment_hash=f"demo-commitment-{slug}",
        seed_hex=f"demo-seed-{slug}", algorithm="SHA256-RANK-v1",
        verification_hash=f"demo-verification-{slug}", executed_at=lot.result_at)
    db.add(draw); db.flush()
    for position, ticket in enumerate(tickets, 1):
        db.add(DrawWinner(draw_id=draw.id, ticket_id=ticket.id,
                          position=position))
db.merge(AppSetting(key="referral_reward",value="20")); db.merge(AppSetting(key="referral_enabled",value="true")); db.merge(AppSetting(key="wallet_topup_deep_link",value="")); db.merge(AppSetting(key="terms_text",value="DhanLaxmi is available only to eligible adults. Lottery participation and wallet credits are subject to applicable laws and verified payment confirmation.")); db.merge(AppSetting(key="privacy_text",value="We use your account, payment reference and delivery information only to operate draws, issue prizes and meet legal obligations.")); db.merge(AppSetting(key="support_contact",value="support@dhanlaxmi.app")); db.commit(); db.close()
print("Seeded. Admin: admin@example.com / ChangeMe123! (change immediately)")
