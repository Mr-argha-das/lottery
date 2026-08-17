from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class Register(BaseModel):
    full_name:str=Field(min_length=2,max_length=100); mobile:str; password:str=Field(min_length=8,max_length=128); referral_code:str|None=None
    @field_validator("mobile")
    @classmethod
    def mobile_ok(cls,v):
        v="".join(c for c in v if c.isdigit())
        if len(v)<10 or len(v)>15: raise ValueError("Invalid mobile")
        return v
class Login(BaseModel): mobile:str; password:str
class Refresh(BaseModel): refresh_token:str
class ProfileUpdate(BaseModel):
    full_name:str|None=None; upi_id:str|None=None; address:str|None=None; city:str|None=None; state:str|None=None; pincode:str|None=None
class LotteryCreate(BaseModel):
    name:str; slug:str; description:str; entry_price:float=Field(gt=0); start_at:datetime; join_deadline:datetime; result_at:datetime; max_tickets:int=Field(gt=0); min_tickets:int=1; status:str="DRAFT"; terms:str=""; banner_url:str|None=None
class PrizeCreate(BaseModel):
    title:str; description:str=""; prize_type:str="CASH"; amount:float|None=None; image_url:str|None=None; quantity:int=1; terms:str=""
class PaymentCreate(BaseModel): lottery_id:str; idempotency_key:str=Field(min_length=8,max_length=100)
class Webhook(BaseModel): payment_id:str; provider_reference:str; status:str; signature:str
class AdminLogin(BaseModel): email:str; password:str
class SettingUpdate(BaseModel): value:str
class LotteryUpdate(BaseModel):
    name:str|None=None; description:str|None=None; entry_price:float|None=Field(default=None,gt=0); start_at:datetime|None=None; join_deadline:datetime|None=None; result_at:datetime|None=None; max_tickets:int|None=Field(default=None,gt=0); min_tickets:int|None=None; status:str|None=None; terms:str|None=None; banner_url:str|None=None
