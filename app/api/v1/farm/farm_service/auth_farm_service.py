from datetime import datetime
from typing import Annotated


from fastapi import Depends
from fastapi.templating import Jinja2Templates
from fastapi_mail import MessageSchema, MessageType
from sqlmodel import select


from app.api.v1.farm.farm_service.otp_farm_service import OtpFarmServiceInstance
from app.database import SessionDB1

from app.mail_farm import MailFarm
from app.model.farm.login import Login



class AuthFarmService:
    def __init__(self, session: SessionDB1, otpService: OtpFarmServiceInstance, mail: MailFarm):
        self.session = session
        self.mail = mail
        self.otpService = otpService
        self.templates = Jinja2Templates(directory="app/templates")
    
    async def sendEmailVerification(self, email: str, username: str):
        login_statement = select(Login).where(Login.Username == username)
        login = self.session.exec(login_statement).first()
        if not login:
            raise Exception("login not found")
        otp = self.otpService.createOTP(username)
        html_content = self.templates.get_template("send_verification_farm.html").render(
            name = login.Username,
            otp = otp,
            expire_minutes = self.otpService.MAX_ATTEMPTS
        )
        message = MessageSchema(
            subject="Email Verification Code",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html
        )
        await self.mail.send_message(
            message
        )
    def verify_email(self, username: str, email: str, code: str):
        is_valid = self.otpService.verifyOTP(username, code)
        if not is_valid:
            raise Exception("invalid or expired OTP")
        login_statement = select(Login).where(Login.Username == username)
        login = self.session.exec(login_statement).first()
        if not login:
            raise Exception("login not found")
        login.Email = email
        login.EmailVerified = datetime.now()
        self.session.add(login)
        self.session.commit()
        
    async def sendforgetpass(self, email: str):
        login_statement = select(Login).where(Login.Email == email)
        result = self.session.exec(login_statement).first()
        if  not result:
            raise Exception("member not found")
        otp = self.otpService.createOTP(Login.Username)
        html_content = self.templates.get_template("send_verification_farm.html").render(
                    name = Login.Username,
                    otp = otp,
                    expire_minutes = self.otpService.MAX_ATTEMPTS
                )
        message = MessageSchema(
                    subject="Email Verification Code",
                    recipients=[email],
                    body=html_content,
                    subtype=MessageType.html
                )
        await self.mail.send_message(
                    message
                )
    
    def verifyforget(self, password: str, code: str):
        is_valid = self.otpService.verifyOTP(password, code)
        if not is_valid:
            raise Exception("invalid or expired OTP")
        login_statement = select(Login).where(Login.Password == password)
        login = self.session.exec(login_statement).first()
        if not login:
            raise Exception("login not found")
        login.Password = password
        self.session.add(login)
        self.session.commit()
        
        
        
def get_auth_service(session: SessionDB1, otpService: OtpFarmServiceInstance, mail: MailFarm) -> AuthFarmService:
    return AuthFarmService(session, otpService, mail)
AuthServiceInstance = Annotated[AuthFarmService, Depends(get_auth_service)]        
            
            
            