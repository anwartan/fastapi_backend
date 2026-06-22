import hashlib
import hmac
import random
from datetime import datetime, timedelta, timezone
import string
from typing import Annotated


from annotated_types import Timezone
from fastapi import Depends
from regex import F
from requests import session
from sqlalchemy import false, true
from sqlmodel import select
from urllib3 import Retry

from app.database import SessionDBKafeLogin
from app.model.kafe.member import Member
class OtpService:
    Max_attempt=5
    
    def __init__(self,session:SessionDBKafeLogin):
        self.session=session
    def generate_otp(self):
        return "".join(random.choices(string.digits,k=6))
    def hash_otp(self,otp:str)->str:
        return hashlib.sha256(otp.encode()).hexdigest()
    def createotp(self,username:str):
        member=self.get_member(username)
        member.TokenOtp=None
        self.session.add(member)
        self.session.commit()
        otp_code=self.generate_otp()
        otp_hash=self.hash_otp(otp_code)
        expired_at=datetime.now()+timedelta(minutes=5)
        member.TokenOtp=otp_hash
        member.TokenAttemptOtp=0
        member.TokenExpiredDate=expired_at
        self.session.add(member)
        self.session.commit()
        return otp_code
        
    def verify_otp(self, otp: str,username:str):
        member=self.get_member(username)
        is_valid=True
        now=datetime.now()
        if member.TokenExpiredDate==None:
            is_valid=False
        elif member.TokenExpiredDate < now:
            is_valid= False
        if member.TokenAttemptOtp ==None or member.TokenAttemptOtp>self.Max_attempt:
            is_valid=False
        if member.TokenOtp is None or hmac.compare_digest(self.hash_otp(otp),member.TokenOtp) == False:
            is_valid=False
            
        if is_valid==False:
            member.TokenAttemptOtp=(member.TokenAttemptOtp or 0)+1
            self.session.add(member)
            self.session.commit()
        return is_valid
    def get_member(self,username:str)->Member:
        member_statement=select(Member).where(Member.Username==username)
        member=self.session.exec(member_statement).first()
        if not member:
            raise Exception("member is not found")
        return member
def get_otp_service(session:SessionDBKafeLogin)->OtpService:
    return OtpService(session)
OtpServiceInstance=Annotated[OtpService,Depends(get_otp_service)]
