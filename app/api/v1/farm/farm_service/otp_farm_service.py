from datetime import datetime , timedelta
import hashlib
import hmac
import random
import string
from typing import Annotated

from fastapi import Depends


from sqlmodel import select

from app.database import SessionDB1
from app.model.farm.login import Login




class OtpFarmService:
    MAX_ATTEMPTS = 5
    def __init__(self, session: SessionDB1):
        self.session = session
        
    def _generateCode(self) -> str:
        return "".join(random.choices(string.digits, k=6))
    
    def _hashOTP(self, otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def createOTP(self, username: str) -> str:
        login = self.get_login(username)
        login.TokenOtp = None
        self.session.add(login)
        self.session.commit()
        otp_code = self. _generateCode()
        otp_hash = self. _hashOTP(otp_code)
        expired_at = datetime.now() + timedelta(minutes=5)
        login.TokenOtp = otp_hash
        login.TokenAttempOtp = 0;
        login.TokenExpiredDateOtp = expired_at
        self.session.add(login)
        self.session.commit()
        return otp_code
    async def verifyOTP(self, username: str, otp_input:str) -> bool:
        login = self.get_login(username)
        is_valid = True
        now = datetime.now()
        if login.TokenExpiredDateOtp == None:
            is_valid = False
        elif login.TokenExpiredDateOtp < now:
            is_valid = False
        if login.TokenAttempOtp == None or login.TokenAttempOtp > self.MAX_ATTEMPTS:
            is_valid = False
        if login.TokenOtp is None or hmac.compare_digest(self._hashOTP(otp_input), login.TokenOtp) == False:
            is_valid = False
        if is_valid == False:
            login.TokenAttempOtp = (login.TokenAttempOtp or 0) + 1
            self.session.add(login)
            self.session.commit()
        return is_valid
        
        
    def get_login(self, username: str) -> Login:
        login_statement = select(Login).where(Login.Username == username)
        login = self.session.exec(login_statement).first()
        if not login:
            raise Exception("login not found")
        return login
    
    
def get_otp_service(session: SessionDB1) -> OtpFarmService:
        return OtpFarmService(session=session)
    
OtpFarmServiceInstance = Annotated[OtpFarmService, Depends(get_otp_service)]